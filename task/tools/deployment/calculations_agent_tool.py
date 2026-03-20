from typing import Any

from task.tools.deployment.base_agent_tool import BaseAgentTool


class CalculationsAgentTool(BaseAgentTool):

    @property
    def deployment_name(self) -> str:
        return "calculations-agent"
    
    @property
    def name(self) -> str:
        return "calculations_agent"
    
    @property
    def description(self) -> str:
        return "Call Calculations Agent to perform mathematical operations, execute Python code, and create visualizations. Use this tool when you need complex calculations, data analysis, or chart generation."
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The request or question to send to the Calculations Agent"
                },
                "propagate_history": {
                    "type": "boolean",
                    "description": "Whether to propagate the full conversation history with this agent",
                    "default": False
                }
            },
            "required": ["prompt"]
        }

