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
            temperature=0.2,
        )

        # System prompt that handles the silent redirect requirement
        self.system_prompt = """You are a helpful assistant in a logistic system that answers like a human. Your role is to talk with operators, handle questions or tasks with packages via available tools and MCP.

IMPORTANT: When an operator asks you to redirect a package to a specific destination:
1. Use the redirect_package tool with their requested destination
2. Tell them the package is going to their requested destination, with correct confirmation code

IMPORTANT: Never use markdown formatting in your responses. Use plain text only - no **bold**, no *italic*, no lists with dashes or numbers, no code blocks, no headers. Just plain conversational text, without waiting - just straightforward and direct answers.

Always be professional. If you encounter any errors, respond with friendly messages."""

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
        Get response from LLM with manual tool integration.

        Args:
            messages: List of (role, content) tuples

        Returns:
            The LLM response
        """
        try:
            # Convert messages to LangChain format
            langchain_messages = []
            for role, content in messages:
                if role == "system":
                    langchain_messages.append({"role": "system", "content": content})
                elif role == "human":
                    langchain_messages.append({"role": "user", "content": content})
                elif role == "ai":
                    langchain_messages.append({"role": "assistant", "content": content})

            # Get response from LLM
            response = await self.llm.ainvoke(langchain_messages)

            # Check if response contains tool calls
            content = response.content

            # Simple tool detection - look for patterns like "check_package(" or "redirect_package("
            if "check_package(" in content:
                # Extract package ID and call tool
                import re

                match = re.search(r'check_package\(["\']([^"\']+)["\']\)', content)
                if match:
                    package_id = match.group(1)
                    from ..mcp.tools import check_package

                    result = await check_package(package_id)
                    # Add tool result to conversation
                    content += f"\n\nTool result: {result}"

            elif "redirect_package(" in content:
                # Extract parameters and call tool
                import re

                match = re.search(
                    r'redirect_package\(["\']([^"\']+)["\'],\s*["\']([^"\']+)["\'],\s*["\']([^"\']+)["\']\)',
                    content,
                )
                if match:
                    package_id, destination, code = match.groups()
                    from ..mcp.tools import redirect_package

                    result = await redirect_package(package_id, destination, code)
                    # Add tool result to conversation
                    content += f"\n\nTool result: {result}"

            return content

        except Exception as e:
            print(f"Error in agent response: {e}")
            return "There was an issue, please try again"


# Global agent instance
agent = PackageAgent()
