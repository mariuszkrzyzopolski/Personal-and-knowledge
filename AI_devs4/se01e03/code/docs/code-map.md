package-service-proxy/
├── .env                    = secrets (API keys, not committed)
├── .env.example            = template for required env vars
├── pyproject.toml          = uv project config + dependencies
├── sessions.json           = session storage (generated at runtime)
├── src/
│   ├── __init__.py         = package marker
│   ├── main.py             = FastAPI app entry point, port 3000
│   ├── config.py           = .env loader
│   ├── mcp/
│   │   ├── __init__.py     = package marker
│   │   └── tools.py        = MCP tools (check_package, redirect_package)
│   ├── agent/
│   │   ├── __init__.py     = package marker
│   │   └── logic.py        = LangChain agent with OpenRouter
│   └── storage/
│       ├── __init__.py     = package marker
│       └── session.py      = JSON session persistence
├── tests/
│   └── test_agent.py       = smoke test for agent + MCP integration
├── docs/
│   └── code-map.md         = this file
├── TODO_feature-packageservice_prime.md  = implementation plan
├── SPEC_PACKAGE_SERVICE_PROXY.md         = locked-in requirements
└── requirements-packageservice.md        = original requirements

# Stack Summary
- HTTP Server: FastAPI (port 3000)
- MCP: fastmcp (embedded in FastAPI)
- LLM: OpenRouter (deepseek-v3.2)
- Agent Framework: LangChain + langchain-mcp
- Config: python-dotenv
- Storage: JSON file (sessions.json)
- Package Manager: uv
