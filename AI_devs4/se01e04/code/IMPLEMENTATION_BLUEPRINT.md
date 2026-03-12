# SPK Automation System - Implementation Blueprint

## Technology Stack Selection

### Core Languages & Frameworks
```
Primary: Python 3.10+
- FastMCP for MCP server implementation
- LangChain/OpenRouter for AI agent
- Tesseract OCR for image text extraction (trasy-wylaczone.png)
- Regular expressions for Polish text parsing
- Pydantic for data validation
- python-dotenv for configuration
- FastAPI for HTTP API server

Secondary Tools:
- OpenRouter API client (openai package with custom endpoint)
- MCP protocol libraries (mcp, mcp-client)
- pytesseract for OCR integration
- Pillow for image preprocessing
- Markdown parsing libraries
- Unit testing (pytest)
```

### Development Environment
```
- Virtual environment: venv or poetry
- Package management: pip/requirements.txt
- Code formatting: black, isort
- Linting: ruff, mypy
- Version control: git
```

## Project Structure to Create

```
/spk-automation/
├── mcp_server/
│   ├── __init__.py
│   ├── server.py                 # Main MCP server implementation
│   ├── config.py                 # Server configuration
│   └── tools/
│       ├── __init__.py
│       ├── route_finder.py       # Parse zalacznik-F.md + trasy-wylaczone.png
│       ├── fee_calculator.py     # Apply Section 9.2 formulas
│       └── declaration_filler.py # Generate zalacznik-E.md format
├── agent/
│   ├── __init__.py
│   ├── main.py                   # AI agent orchestration (HTTP API)
│   ├── document_parser.py        # Polish .md parsing with SPK terminology
│   ├── ocr_processor.py          # OCR for trasy-wylaczone.png
│   └── orchestrator.py           # Tool calling and workflow management
├── core/
│   ├── __init__.py
│   ├── models.py                 # Pydantic models for SPK data
│   ├── constants.py              # SPK constants and enums
│   └── business_rules.py         # Business logic implementation
├── config/
│   ├── openrouter.yaml           # OpenRouter API configuration
│   ├── system_rules.json         # SPK business rules (parsed from docs)
│   └── mcp_config.json           # MCP server configuration
├── tests/
│   ├── __init__.py
│   ├── test_gdansk_zarnowiec.py  # Acceptance test case
│   ├── test_fee_calculator.py
│   ├── test_route_finder.py
│   └── test_declaration_format.py
├── data/
│   └── transport_docs/           # Symlink/copy of original docs
├── scripts/
│   ├── setup_environment.sh
│   └── run_tests.sh
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

## Component Implementation Details

### 1. MCP Server (`mcp_server/server.py`)

```python
# Core structure
from mcp import Client, Server
from mcp.server import Server
from mcp.server.models import (
    CallToolRequest,
    ListToolsRequest,
    Tool,
    TextContent,
    ImageContent,
)

class SPKMCPServer:
    def __init__(self):
        self.tools = {
            "route_finder": Tool(
                name="route_finder",
                description="Find route between cities using SPK route diagrams",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "origin": {"type": "string"},
                        "destination": {"type": "string"},
                        "category": {"type": "string", "enum": ["A", "B", "C", "D", "E"]}
                    },
                    "required": ["origin", "destination", "category"]
                }
            ),
            # ... other tools
        }
    
    async def handle_call_tool(self, request: CallToolRequest):
        # Route to appropriate tool implementation
        pass
```

### 2. Route Finder Tool (`mcp_server/tools/route_finder.py`)

```python
class RouteFinder:
    def __init__(self, route_diagram_path, closed_routes_image_path):
        self.route_diagram = self.parse_zalacznik_f(route_diagram_path)
        self.closed_routes = self.analyze_closed_routes_image(closed_routes_image_path)
    
    def parse_zalacznik_f(self, filepath):
        """Parse the ASCII route diagram from zalacznik-F.md"""
        # Implementation: parse lines, extract nodes and connections
        # Identify: ===X=== (closed), ------- (magistral), xxxxxxx (regional)
        pass
    
    def find_route(self, origin, destination, category):
        """Find route considering closed route access rules"""
        if destination == "Żarnowiec":
            if category not in ["A", "B"]:
                raise ValueError("Żarnowiec accessible only for categories A/B")
            return self.find_zarnowiec_route(origin)
        else:
            return self.find_standard_route(origin, destination)
```

### 3. Fee Calculator Tool (`mcp_server/tools/fee_calculator.py`)

```python
class FeeCalculator:
    def __init__(self, business_rules):
        self.rules = business_rules
    
    def calculate(self, category, weight_kg, distance_km, regional_boundaries):
        """Calculate fee with Category A/B exemptions"""
        # Implement progressive weight fee calculation
        # Apply category-based exemptions
        # Include additional wagon calculations
        pass
    
    def get_wdp(self, category, weight_kg):
        """Calculate WDP (additional wagons) field"""
        pass
```

### 4. Declaration Filler Tool (`mcp_server/tools/declaration_filler.py`)

```python
class DeclarationFiller:
    TEMPLATE = """SYSTEM PRZESYŁEK KONDUKTORSKICH - DEKLARACJA ZAWARTOŚCI
======================================================
DATA: {date}
PUNKT NADAWCZY: {origin}
------------------------------------------------------
NADAWCA: {sender_id}
PUNKT DOCELOWY: {destination}
TRASA: {route_code}
------------------------------------------------------
KATEGORIA PRZESYŁKI: {category}
------------------------------------------------------
OPIS ZAWARTOŚCI (max 200 znaków): {content}
------------------------------------------------------
DEKLAROWANA MASA (kg): {weight}
------------------------------------------------------
WDP: {wdp}
------------------------------------------------------
UWAGI SPECJALNE: {special_notes}
------------------------------------------------------
KWOTA DO ZAPŁATY: {fee} PP
------------------------------------------------------
OŚWIADCZAM, ŻE PODANE INFORMACJE SĄ PRAWDZIWE.
BIORĘ NA SIEBIE KONSEKWENCJĘ ZA FAŁSZYWE OŚWIADCZENIE.
======================================================"""
    
    def fill(self, data):
        """Fill template with data, ensuring exact format match"""
        # Validate against zalacznik-E.md format
        # Ensure Polish text encoding
        # Date format: YYYY-MM-DD
        pass
```

### 5. AI Agent (`agent/main.py`)

```python
class SPKAgent:
    def __init__(self, mcp_client, openrouter_client, model_config):
        self.mcp = mcp_client
        self.llm = openrouter_client
        self.model_config = model_config
        self.document_parser = PolishDocumentParser()
        self.ocr_processor = OCRProcessor()
    
    async def process_package_request(self, request):
        """
        Full workflow:
        1. Parse request parameters
        2. Extract text from trasy-wylaczone.png via OCR
        3. Parse zalacznik-F.md text
        4. Call route_finder tool (uses both text sources)
        5. Call fee_calculator tool  
        6. Call declaration_filler tool
        7. Validate output (happy path only)
        8. Return declaration
        """
        pass
```

## Data Models (`core/models.py`)

```python
from pydantic import BaseModel, Field, validator
from enum import Enum
from datetime import date

class PackageCategory(str, Enum):
    STRATEGIC = "A"
    MEDICAL = "B"
    FOOD = "C"
    ECONOMIC = "D"
    PERSONAL = "E"

class PackageRequest(BaseModel):
    sender_id: str = Field(..., pattern=r'^\d{9}$')  # 9-digit identifier
    origin: str
    destination: str
    weight_kg: float = Field(..., gt=0.0, le=4000.0)
    category: PackageCategory
    content: str = Field(..., max_length=200)
    special_notes: str = ""
    budget_pp: float = 0.0
    # Note: date is NOT included - will be system date at generation time
    
    @validator('destination')
    def validate_zarnowiec_access(cls, v, values):
        if v == 'Żarnowiec' and values.get('category') not in [PackageCategory.STRATEGIC, PackageCategory.MEDICAL]:
            raise ValueError('Żarnowiec accessible only for Strategic/Medical packages')
        return v

class RouteResult(BaseModel):
    route_code: str
    distance_km: float
    regional_boundaries: int
    uses_closed_route: bool = False
    requires_special_authorization: bool = False

class FeeResult(BaseModel):
    base_fee: float
    weight_fee: float
    route_fee: float
    additional_wagons: int
    additional_wagon_fee: float
    total: float
    wdp: int  # Wagony Dodatkowe Płatne

class Declaration(BaseModel):
    content: str
    is_valid_format: bool
    date_generated: datetime  # System date at generation time
    validation_errors: list[str] = []  # Empty for happy path
```

## Configuration Files

### `requirements.txt`
```
fastmcp>=0.3.0
openai>=1.0.0
langchain>=0.1.0
pillow>=10.0.0
pytesseract>=0.3.10
pydantic>=2.0.0
python-dotenv>=1.0.0
fastapi>=0.104.0
uvicorn>=0.24.0
httpx>=0.25.0
aiohttp>=3.9.0
```

### `config/openrouter.yaml`
```yaml
openrouter:
  api_key: ${OPENROUTER_API_KEY}
  base_url: "https://openrouter.ai/api/v1"
  models:
    default: "deepseek/deepseek-v3.2"
    alternatives:
      - "google/gemini-2.0-flash-exp:free"
      - "meta-llama/llama-3.3-70b-instruct:free"
      - "openai/gpt-4o-mini"
  temperature: 0.1
  max_tokens: 2000
  
language:
  default: "pl"
  supported: ["pl", "en"]
  
spk_terminology:
  file: "config/spk_terminology.json"
  
ocr:
  engine: "tesseract"
  language: "pol"
  preprocessing: true
  
server:
  host: "0.0.0.0"
  port: 8000
  mode: "http"
```

### `config/system_rules.json`
```json
{
  "categories": {
    "A": {"name": "Strategic", "base_fee": 0, "exemptions": ["weight", "route", "wagons"]},
    "B": {"name": "Medical", "base_fee": 0, "exemptions": ["weight", "route", "wagons"]},
    "C": {"name": "Food", "base_fee": 2, "exemptions": []},
    "D": {"name": "Economic", "base_fee": 5, "exemptions": []},
    "E": {"name": "Personal", "base_fee": 10, "exemptions": []}
  },
  "weight_fee_brackets": [
    {"max": 5, "rate": 0.5},
    {"max": 25, "rate": 1.0},
    {"max": 100, "rate": 2.0},
    {"max": 500, "rate": 3.0},
    {"max": 1000, "rate": 5.0},
    {"max": null, "rate": 7.0}
  ],
  "closed_route_destinations": ["Żarnowiec"],
  "closed_route_allowed_categories": ["A", "B"]
}
```

## Build & Development Scripts

### `scripts/setup_environment.sh`
```bash
#!/bin/bash
# Setup development environment

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Copy transport docs to data directory
mkdir -p data
cp -r ../transport_docs data/

echo "Setup complete. Activate with: source venv/bin/activate"
```

### `scripts/run_tests.sh`
```bash
#!/bin/bash
# Run test suite

source venv/bin/activate
pytest tests/ -v

# Run acceptance test specifically
python -m pytest tests/test_gdansk_zarnowiec.py -v
```

## Testing Strategy

### Unit Tests
- Test each tool in isolation
- Test business logic functions
- Test data model validation

### Integration Tests
- Test MCP server with tools
- Test agent with MCP client
- Test OpenRouter integration
- Test OCR processing (text extraction only)

### Acceptance Test (`tests/test_gdansk_zarnowiec.py`)
- **ONLY test M1 acceptance scenario** (happy path)
- No error handling tests
- No edge case tests
```python
def test_gdansk_to_zarnowiec_strategic():
    """M1: Acceptance test case"""
    request = PackageRequest(
        sender_id="450202122",
        origin="Gdańsk",
        destination="Żarnowiec",
        weight_kg=2800,
        category=PackageCategory.STRATEGIC,
        content="kasety z paliwem do reaktora",
        special_notes="brak",
        budget_pp=0
    )
    
    # Process through full system
    result = agent.process_package_request(request)
    
    # Assertions
    assert result.fee_result.total == 0
    assert result.route_result.uses_closed_route
    assert result.declaration.is_valid_format
    assert "0 PP" in result.declaration.content
    assert "KATEGORIA PRZESYŁKI: A" in result.declaration.content
```

## Deployment & Execution

### Running the System
```bash
# 1. Start MCP server (HTTP mode)
python -m mcp_server.server --mode http --port 8000

# 2. Test HTTP API endpoint (single agent system)
curl -X POST http://localhost:8000/process-package \
  -H "Content-Type: application/json" \
  -d '{
    "sender_id": "450202122",
    "origin": "Gdańsk",
    "destination": "Żarnowiec",
    "weight_kg": 2800,
    "category": "A",
    "content": "kasety z paliwem do reaktora",
    "special_notes": "brak",
    "budget_pp": 0
  }'
```

### Environment Variables
```bash
# .env file
OPENROUTER_API_KEY=your_key_here
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8000
LOG_LEVEL=INFO
```

## Anti-Goal Prevention

### Polish Text Handling
- Use proper Unicode encoding
- Validate Polish diacritics
- Test with actual Polish documents

### Format Compliance
- Exact match with `zalacznik-E.md`
- Line-by-line comparison in tests
- Template validation

### OpenRouter Integration
- Proper API client configuration
- Model selection for Polish language
- Error handling for API failures

## Next Steps Implementation Order

1. **Setup project structure** and virtual environment
2. **Implement core data models** and business logic
3. **Build MCP server** with three tools
4. **Create AI agent** with OpenRouter integration
5. **Write comprehensive tests** including acceptance test
6. **Document and validate** against all requirements
7. **Deploy and test** with actual SPK documentation