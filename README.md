# Pueue Wrapper

Python wrapper for [Pueue](https://github.com/Nukesor/pueue)

```bash
# NOTE: currently the latest version of pueue is 4.0.0
brew install pueue
brew services start pueue
```

```bash
uv install

# test pueue wrapper
python pueue_wrapper.py

# test api
python -m uvicorn api:app --reload
# http://127.0.0.1:8000/docs
```

---

Try to simplify this: [ML-API-Submit-Template/pueue.py at main · daviddwlee84/ML-API-Submit-Template](https://github.com/daviddwlee84/ML-API-Submit-Template/blob/main/pueue.py)

TODO: use latest syntax (if anything changed) [Release v4.0.0 · Nukesor/pueue](https://github.com/Nukesor/pueue/releases/tag/v4.0.0)
