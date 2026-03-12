from typing import Any, Dict
from mcp_server.tools.route_finder import RouteFinder
from mcp_server.tools.fee_calculator import FeeCalculator
from mcp_server.tools.declaration_filler import DeclarationFiller


class SPKMCPServer:
    def __init__(self):
        self.route_finder = RouteFinder()
        self.fee_calculator = FeeCalculator()
        self.declaration_filler = DeclarationFiller()
        self.tools = {
            "route_finder": {
                "name": "route_finder",
                "description": "Find route between cities using SPK route diagrams",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "origin": {"type": "string"},
                        "destination": {"type": "string"},
                        "category": {
                            "type": "string",
                            "enum": ["A", "B", "C", "D", "E"],
                        },
                    },
                    "required": ["origin", "destination", "category"],
                },
            },
            "fee_calculator": {
                "name": "fee_calculator",
                "description": "Calculate shipping fee based on category, weight, distance, and regional boundaries",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": ["A", "B", "C", "D", "E"],
                        },
                        "weight_kg": {"type": "number"},
                        "distance_km": {"type": "number"},
                        "regional_boundaries": {"type": "integer"},
                    },
                    "required": [
                        "category",
                        "weight_kg",
                        "distance_km",
                        "regional_boundaries",
                    ],
                },
            },
            "declaration_filler": {
                "name": "declaration_filler",
                "description": "Generate package declaration in exact SPK format",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sender_id": {"type": "string"},
                        "origin": {"type": "string"},
                        "destination": {"type": "string"},
                        "route_code": {"type": "string"},
                        "category": {"type": "string"},
                        "content": {"type": "string"},
                        "weight_kg": {"type": "number"},
                        "wdp": {"type": "integer"},
                        "special_notes": {"type": "string"},
                        "fee": {"type": "number"},
                        "date": {"type": "string"},
                    },
                    "required": [
                        "sender_id",
                        "origin",
                        "destination",
                        "route_code",
                        "category",
                        "content",
                        "weight_kg",
                        "wdp",
                        "fee",
                    ],
                },
            },
        }

    async def handle_call_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        if tool_name == "route_finder":
            return self.route_finder.find_route(
                origin=arguments["origin"],
                destination=arguments["destination"],
                category=arguments["category"],
            )
        elif tool_name == "fee_calculator":
            return self.fee_calculator.calculate(
                category=arguments["category"],
                weight_kg=arguments["weight_kg"],
                distance_km=arguments["distance_km"],
                regional_boundaries=arguments["regional_boundaries"],
            )
        elif tool_name == "declaration_filler":
            return {
                "declaration": self.declaration_filler.fill(
                    sender_id=arguments["sender_id"],
                    origin=arguments["origin"],
                    destination=arguments["destination"],
                    route_code=arguments["route_code"],
                    category=arguments["category"],
                    content=arguments["content"],
                    weight_kg=arguments["weight_kg"],
                    wdp=arguments["wdp"],
                    special_notes=arguments.get("special_notes", "brak"),
                    fee=arguments["fee"],
                    date=arguments.get("date"),
                )
            }
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    def list_tools(self):
        return list(self.tools.values())
