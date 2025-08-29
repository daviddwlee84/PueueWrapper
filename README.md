# Pueue Wrapper

Python wrapper for [Pueue](https://github.com/Nukesor/pueue)

```bash
# NOTE: currently the latest version of pueue is 4.0.0
brew install pueue
brew services start pueue
```

```bash
uv sync --all-groups

# FastAPI
pueue-api-server --host 127.0.0.1 --port 8001 --reload

# Streamlit UI
pueue-ui-server

```

---

Try to simplify this: [ML-API-Submit-Template/pueue.py at main · daviddwlee84/ML-API-Submit-Template](https://github.com/daviddwlee84/ML-API-Submit-Template/blob/main/pueue.py)

TODO: use latest syntax (if anything changed) [Release v4.0.0 · Nukesor/pueue](https://github.com/Nukesor/pueue/releases/tag/v4.0.0)

TODO: try to build a MCP server around this (or find MCP server that can directly use any CLI tool)
