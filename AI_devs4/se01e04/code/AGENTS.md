# SPK Package Automation Agent - Execution Plan
## Current State: READY_FOR_IMPLEMENTATION

### IMMEDIATE TASKS:
1. **Setup Phase** (PRIORITY: HIGH)
   - Initialize Python project with MCP dependencies
   - Configure OpenRouter API integration with multiple model support
   - Set up environment for Polish text processing and OCR

2. **MCP Server Implementation** (PRIORITY: HIGH)
   - Implement route_finder.py tool (parse zalacznik-F.md + OCR trasy-wylaczone.png)
   - Implement fee_calculator.py tool (apply Section 9.2 formulas with Category A exemptions)
   - Implement declaration_filler.py tool (generate exact zalacznik-E.md format)
   - Set up HTTP server for single-agent system

3. **AI Agent Core** (PRIORITY: MEDIUM)
   - Build document parser for Polish .md files
   - Implement OCR for trasy-wylaczone.png (text extraction only)
   - Create agent orchestration logic with HTTP API

4. **Żarnowiec Special Handling** (PRIORITY: HIGH)
   - Implement closed-route routing logic per Section 8.3
   - Ensure 0 PP cost calculation with wagon exemptions
   - Use current system date for declarations

5. **Model Comparison & Testing** (PRIORITY: MEDIUM)
   - Test multiple OpenRouter models for Polish language performance
   - Configure model selection via config file
   - Test only M1 acceptance scenario (Gdańsk-Żarnowiec, 2800kg, 0 budget)

### EXECUTION RULES:
- MUST use OpenRouter for model connectivity (anti-goal: model not connected to openrouter)
- MUST handle Polish text and documents (anti-goal: agent not handling polish text)
- MUST follow exact declaration format from zalacznik-E.md
- MUST calculate routes using zalacznik-F.md and OCR of trasy-wylaczone.png
- MUST plan through closed routes for Żarnowiec strategic shipments
- MUST achieve 0 PP cost for Category A packages
- MUST implement HTTP API (not CLI or REPL)
- MUST use current system date in declarations (YYYY-MM-DD format)
- MUST implement OCR for image text extraction (not visual analysis)
- MUST support multiple model configuration
- MUST focus only on happy path (no error handling for edge cases)