"""Entry point – run with: uv run analyze  or  python -m src.main"""

from .agent import run_agent_loop


def main() -> None:
    run_agent_loop()


if __name__ == "__main__":
    main()
