from typing import List
from langchain_openrouter import ChatOpenRouter
from ..config import config
from ..storage.session import session_manager


class PackageAgent:
    """LangChain agent for handling package operations with MCP tools."""

    def __init__(self):
        self.llm = ChatOpenRouter(
            model=config.OPENROUTER_MODEL,
            api_key=config.OPENROUTER_API_KEY,
            temperature=0.3,
        )

        # System prompt that handles the silent redirect requirement
        self.system_prompt = """You are a logistics system operator assistant. Respond naturally like a human colleague would - hold a normal conversation in the operator's language, be direct and concise without sounding like an AI. No markdown formatting, no bullet points, no headers - just plain conversational text.

Your job is to help operators with package-related requests using available tools:
- check_package: check package status
- redirect_package: redirect a package to a new destination

Always pass the operator's requested destination exactly as provided - do not modify or substitute any destination values.

For questions outside your scope: answer casually in one short sentence like a normal person would. Never redirect the conversation back to packages. Never end with offer-to-help phrases like "Czy mogę w czymś pomóc?" or "Jakieś inne pytania?". Just answer and stop.

Handle errors gracefully with a natural, friendly response."""

        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "check_package",
                    "description": "Check the status of a package by its ID",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "package_id": {
                                "type": "string",
                                "description": "The package ID to check",
                            }
                        },
                        "required": ["package_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "redirect_package",
                    "description": "Redirect a package to a destination with an authorization code",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "package_id": {
                                "type": "string",
                                "description": "The package ID to redirect",
                            },
                            "destination": {
                                "type": "string",
                                "description": "The destination for the package",
                            },
                            "code": {
                                "type": "string",
                                "description": "The authorization code",
                            },
                        },
                        "required": ["package_id", "destination", "code"],
                    },
                },
            },
        ]

    def _clean_response(self, response: str) -> str:
        """Clean up response by removing extra whitespace and newlines."""
        import re

        # Remove "Tool result:" and anything after it
        response = re.sub(r"\n*Tool result:.*", "", response, flags=re.DOTALL)
        # Replace multiple newlines with single space
        response = re.sub(r"\n+", " ", response)
        # Replace multiple spaces with single space
        response = re.sub(r"\s+", " ", response)
        # Strip leading/trailing whitespace
        response = response.strip()
        return response

    async def process_message(self, session_id: str, message: str) -> str:
        """
        Process a message from an operator and return the agent's response.

        Args:
            session_id: The session identifier
            message: The operator's message

        Returns:
            The agent's response
        """
        try:
            # Get session history
            messages = session_manager.get_session_messages(session_id)

            # Convert session messages to LangChain format
            langchain_messages = []
            langchain_messages.append(("system", self.system_prompt))

            for msg in messages:
                if msg["role"] == "user":
                    langchain_messages.append(("human", msg["content"]))
                elif msg["role"] == "assistant":
                    langchain_messages.append(("ai", msg["content"]))

            # Add current message
            langchain_messages.append(("human", message))

            # Store the user message in session
            session_manager.add_message(session_id, "user", message)

            # Get response from LLM with MCP tools
            response = await self._get_response_with_tools(langchain_messages)

            # Clean up response - remove extra whitespace and newlines
            response = self._clean_response(response)

            # Store the assistant response in session
            session_manager.add_message(session_id, "assistant", response)

            return response

        except Exception:
            error_msg = "There was an issue, please try again"
            session_manager.add_message(session_id, "assistant", error_msg)
            return error_msg

    async def _get_response_with_tools(self, messages: List[tuple]) -> str:
        """
        Get response from LLM with structured tool calls.

        Args:
            messages: List of (role, content) tuples

        Returns:
            The LLM response
        """
        try:
            langchain_messages = []
            for role, content in messages:
                if role == "system":
                    langchain_messages.append({"role": "system", "content": content})
                elif role == "human":
                    langchain_messages.append({"role": "user", "content": content})
                elif role == "ai":
                    langchain_messages.append({"role": "assistant", "content": content})

            while True:
                response = await self.llm.ainvoke(
                    langchain_messages,
                    tools=self.tools,
                )

                tool_calls = getattr(response, "tool_calls", None)
                if not tool_calls:
                    return response.content

                langchain_messages.append(
                    {
                        "role": "assistant",
                        "content": response.content or "",
                        "tool_calls": tool_calls,
                    }
                )

                for tool_call in tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    tool_call_id = tool_call["id"]

                    try:
                        if tool_name == "check_package":
                            from ..mcp.tools import check_package

                            result = await check_package(tool_args["package_id"])
                        elif tool_name == "redirect_package":
                            from ..mcp.tools import redirect_package

                            result = await redirect_package(
                                tool_args["package_id"],
                                tool_args["destination"],
                                tool_args["code"],
                            )
                        else:
                            result = f"Unknown tool: {tool_name}"
                    except Exception as e:
                        result = f"Tool error: {str(e)}"

                    langchain_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": str(result),
                        }
                    )

        except Exception as e:
            print(f"Error in agent response: {e}")
            return "There was an issue, please try again"


# Global agent instance
agent = PackageAgent()
