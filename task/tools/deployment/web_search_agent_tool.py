from typing import Any

from task.tools.deployment.base_agent_tool import BaseAgentTool


class WebSearchAgentTool(BaseAgentTool):

    @property
    def deployment_name(self) -> str:
        return "web-search-agent"
    
    @property
    def name(self) -> str:
        return "web_search_agent"
    
    @property
    def description(self) -> str:
        return "Call Web Search Agent to find information on the internet. Use this tool to search for current events, recent data, weather forecasts, or any information that requires web research."
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The search query or question to send to the Web Search Agent"
                },
                "propagate_history": {
                    "type": "boolean",
                    "description": "Whether to propagate the full conversation history with this agent",
                    "default": False
                }
            },
            "required": ["prompt"]
        }
