import json
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any

from aidial_client import AsyncDial
from aidial_sdk.chat_completion import Message, Role, CustomContent, Stage, Attachment
from pydantic import StrictStr

from task.tools.base_tool import BaseTool
from task.tools.models import ToolCallParams
from task.utils.stage import StageProcessor


class BaseAgentTool(BaseTool, ABC):

    def __init__(self, endpoint: str):
        self.endpoint = endpoint

    @property
    @abstractmethod
    def deployment_name(self) -> str:
        pass

    async def _execute(self, tool_call_params: ToolCallParams) -> str | Message:
        # 1. Get prompt and propagate_history parameters
        arguments = json.loads(tool_call_params.tool_call.function.arguments)
        prompt = arguments.get("prompt", "")
        propagate_history = arguments.get("propagate_history", False)
        
        # 2. Create AsyncDial client and call the agent with streaming
        client: AsyncDial = AsyncDial(
            base_url=self.endpoint,
            api_key=tool_call_params.api_key,
            api_version='2025-01-01-preview'
        )
        
        messages = self._prepare_messages(tool_call_params)
        
        chunks = await client.chat.completions.create(
            messages=messages,
            stream=True,
            deployment_name=self.deployment_name,
            extra_headers={
                "x-conversation-id": tool_call_params.conversation_id
            }
        )
        
        # 3. Prepare variables for collecting streamed data
        content = ''
        custom_content: CustomContent = CustomContent(attachments=[])
        stages_map: dict[int, Stage] = {}
        
        # 4. Iterate through chunks
        async for chunk in chunks:
            if chunk.choices and len(chunk.choices) > 0:
                choice = chunk.choices[0]
                delta = choice.delta
                
                # Stream content to stage
                if delta and delta.content:
                    if tool_call_params.stage:
                        tool_call_params.stage.append_content(delta.content)
                    content += delta.content
                
                # Handle custom_content
                if choice.custom_content:
                    response_custom_content = choice.custom_content
                    
                    # Set state from response
                    if response_custom_content.state:
                        custom_content.state = response_custom_content.state
                    
                    # Propagate attachments to choice
                    if response_custom_content.attachments:
                        for attachment in response_custom_content.attachments:
                            custom_content.attachments.append(attachment)
                            tool_call_params.choice.add_attachment(attachment)
                    
                    # Optional: Stages propagation
                    custom_content_dict = response_custom_content.dict(exclude_none=True)
                    if 'stages' in custom_content_dict:
                        for stage_data in custom_content_dict['stages']:
                            stage_index = stage_data.get('index')
                            
                            if stage_index not in stages_map:
                                # Create new stage
                                stage_name = stage_data.get('name', f'Stage {stage_index}')
                                stages_map[stage_index] = StageProcessor.open_stage(
                                    choice=tool_call_params.choice,
                                    name=stage_name
                                )
                            
                            propagated_stage = stages_map[stage_index]
                            
                            # Propagate stage name
                            if stage_data.get('name'):
                                propagated_stage.append_name(stage_data['name'])
                            
                            # Propagate content
                            if stage_data.get('content'):
                                propagated_stage.append_content(stage_data['content'])
                            
                            # Propagate attachments
                            if stage_data.get('attachments'):
                                for attachment_data in stage_data['attachments']:
                                    attachment = Attachment(**attachment_data)
                                    propagated_stage.add_attachment(attachment)
                            
                            # Close stage if completed
                            if stage_data.get('status') == 'completed':
                                StageProcessor.close_stage_safely(propagated_stage)
        
        # 5. Ensure all stages are closed
        for stage in stages_map.values():
            StageProcessor.close_stage_safely(stage)
        
        # 6. Return Tool message
        return Message(
            role=Role.TOOL,
            content=content,
            tool_call_id=StrictStr(tool_call_params.tool_call.id),
            custom_content=custom_content
        )

    def _prepare_messages(self, tool_call_params: ToolCallParams) -> list[dict[str, Any]]:
        # 1. Get prompt and propagate_history params
        arguments = json.loads(tool_call_params.tool_call.function.arguments)
        prompt = arguments.get("prompt", "")
        propagate_history = arguments.get("propagate_history", False)
        
        # 2. Prepare empty messages array
        messages: list[dict[str, Any]] = []
        
        # 3. Collect proper history if propagate_history is True
        if propagate_history:
            for i, message in enumerate(tool_call_params.messages):
                # Check if this is an assistant message with state containing history for this agent
                if message.role == Role.ASSISTANT:
                    if message.custom_content and message.custom_content.state:
                        state = message.custom_content.state
                        # Check if history for this agent (self.name) exists in state
                        if self.name in state:
                            agent_history = state[self.name]
                            # Add the preceding user message
                            if i > 0 and tool_call_params.messages[i - 1].role == Role.USER:
                                prev_msg = tool_call_params.messages[i - 1]
                                messages.append({
                                    "role": prev_msg.role.value,
                                    "content": prev_msg.content
                                })
                            
                            # Add assistant message with refactored state
                            assistant_msg = deepcopy(message)
                            # Replace the entire state with just the agent-specific history
                            assistant_msg.custom_content.state = agent_history
                            messages.append(assistant_msg.dict(exclude_none=True))
        
        # 4. Add the user message with prompt
        user_message = {
            "role": Role.USER.value,
            "content": prompt
        }
        
        # Include custom_content if there are attachments from the last user message
        if tool_call_params.messages:
            last_message = tool_call_params.messages[-1]
            if last_message.role == Role.USER and last_message.custom_content:
                user_message["custom_content"] = last_message.custom_content.dict(exclude_none=True)
        
        messages.append(user_message)
        
        return messages