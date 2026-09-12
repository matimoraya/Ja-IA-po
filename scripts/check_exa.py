"""Prueba opt-in que hace UNA búsqueda real y consume créditos Exa."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.tools import research_security_context


async def main():
    result = await research_security_context("SSH brute force detection and mitigation official documentation")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] and result["data"]["sources"] else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
