import os

import uvicorn
from aidial_sdk import DIALApp
from aidial_sdk.chat_completion import ChatCompletion, Request, Response

from task.agents.calculations.calculations_agent import CalculationsAgent
from task.agents.calculations.tools.simple_calculator_tool import SimpleCalculatorTool
from task.tools.base_tool import BaseTool
from task.agents.calculations.tools.py_interpreter.python_code_interpreter_tool import PythonCodeInterpreterTool
from task.tools.deployment.content_management_agent_tool import ContentManagementAgentTool
from task.tools.deployment.web_search_agent_tool import WebSearchAgentTool
from task.utils.constants import DIAL_ENDPOINT, DEPLOYMENT_NAME


class CalculationsApplication(ChatCompletion):
    
    async def chat_completion(self, request: Request, response: Response) -> None:
        # Prepare tools
        tools: list[BaseTool] = [
            SimpleCalculatorTool(),
            PythonCodeInterpreterTool(),
            ContentManagementAgentTool(endpoint=DIAL_ENDPOINT),
            WebSearchAgentTool(endpoint=DIAL_ENDPOINT)
        ]
        
        # Create agent
        agent = CalculationsAgent(
            endpoint=DIAL_ENDPOINT,
            tools=tools
        )
        
        # Create choice
        choice = response.create_single_choice()
        
        # Handle request
        await agent.handle_request(
            deployment_name=DEPLOYMENT_NAME,
            choice=choice,
            request=request,
            response=response
        )


# Create DIAL app
app = DIALApp(
    description="Calculations Agent Application",
    add_healthcheck=True,
)

app.add_chat_completion("calculations-agent", CalculationsApplication())


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)