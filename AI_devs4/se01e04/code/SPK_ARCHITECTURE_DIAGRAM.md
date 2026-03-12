# SPK Package Automation System Architecture

## System Overview Diagram

```mermaid
graph TD
    subgraph "External Systems"
        O[OpenRouter API]
        D[transport_docs/]
    end
    
    subgraph "AI Agent Layer"
        A[SPK Agent]
        P[Polish Document Parser]
        I[OCR Processor<br/>trasy-wylaczone.png]
        O[Orchestrator]
    end
    
    subgraph "MCP Server Layer"
        M[MCP Server<br/>HTTP API]
        T1[Route Finder Tool<br/>parses zalacznik-F.md + OCR result]
        T2[Fee Calculator Tool<br/>applies Section 9.2 formulas]
        T3[Declaration Filler Tool<br/>generates zalacznik-E.md format]
    end
    
    subgraph "Business Logic"
        B1[Category A Rules]
        B2[Żarnowiec Closed-Route Logic]
        B3[Wagon Calculation]
        B4[0 PP Budget Constraint]
    end
    
    D --> P
    D --> I
    P --> O
    I --> O
    O --> M
    M --> T1
    M --> T2
    M --> T3
    T1 --> B2
    T2 --> B1
    T2 --> B3
    T2 --> B4
    O --> A
    
    A --> OUT[Package Declaration]
```

## Component Descriptions

### 1. AI Agent Layer
- **SPK Agent**: Main orchestrator that coordinates document parsing, image analysis, and tool calls
- **Polish Document Parser**: Specialized parser for Polish .md files with technical terminology
- **Image Analyzer**: Processes `trasy-wylaczone.png` to extract route closure information
- **Orchestrator**: Sequences operations and manages tool invocations

### 2. MCP Server Layer
- **MCP Server**: Implements Model Context Protocol with three custom tools
- **Route Finder Tool**: Analyzes route diagrams to find paths between cities
- **Fee Calculator Tool**: Applies SPK fee formulas with category-based exemptions
- **Declaration Filler Tool**: Generates declarations in exact `zalacznik-E.md` format

### 3. Business Logic Layer
- **Category A Rules**: Implements strategic package exemptions (0 PP fees, closed-route access)
- **Żarnowiec Closed-Route Logic**: Special handling for excluded zones per Section 8.3
- **Wagon Calculation**: Determines wagon requirements based on weight (500kg per wagon)
- **0 PP Budget Constraint**: Ensures final cost meets budget requirements

## Data Flow

1. **Document Ingestion**: Polish .md files and .png images are parsed
2. **Route Analysis**: Route finder identifies Gdańsk-Żarnowiec path via closed routes
3. **Fee Calculation**: Applies Category A exemptions to achieve 0 PP cost
4. **Declaration Generation**: Produces final declaration matching exact template format
5. **Validation**: Ensures all anti-goals are avoided (Polish handling, format compliance, OpenRouter connectivity)

## Integration Points
- **OpenRouter API**: Used for AI model inference with Polish language support
- **MCP Protocol**: Standardized tool calling interface for AI agents
- **File System**: Reads from `transport_docs/` directory for all SPK documentation