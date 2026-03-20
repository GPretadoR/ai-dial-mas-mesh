from typing import Any

from task.tools.deployment.base_agent_tool import BaseAgentTool


class ContentManagementAgentTool(BaseAgentTool):

    @property
    def deployment_name(self) -> str:
        return "content-management-agent"
    
    @property
    def name(self) -> str:
        return "content_management_agent"
    
    @property
    def description(self) -> str:
        return "Call Content Management Agent to extract and analyze document content. Use this tool to read files, search through documents, or answer questions based on document content (PDF, TXT, CSV, HTML files)."
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The request or question to send to the Content Management Agent"
                },
                "propagate_history": {
                    "type": "boolean",
                    "description": "Whether to propagate the full conversation history with this agent",
                    "default": False
                }
            },
            "required": ["prompt"]
        }
