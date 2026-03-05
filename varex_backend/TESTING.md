# Backend Testing Guide

This guide ensures the backend test command runs cleanly:

```bash
python -m pytest -q tests/test_calculators_api.py
```

## 1) Create and activate venv

### Windows (PowerShell)

```powershell
cd c:\Users\ThrinathaReddy\PycharmProjects\VERTEX\varex_backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

### Linux/macOS

```bash
cd /path/to/VERTEX/varex_backend
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
```

## 2) Install dependencies

```bash
python -m pip install -r requirements.txt
```

## 3) Verify critical packages

```bash
python -c "import pydantic_settings, pytest, pytest_asyncio, aiosqlite; print('deps-ok')"
```

## 4) Run calculator API regression tests

```bash
python -m pytest -q tests/test_calculators_api.py
```

## 5) Optional: run full backend test suite

```bash
python -m pytest -q
```

## Notes

- Always run tests from the `varex_backend` directory.
- If `pytest` command is not found, use `python -m pytest ...` (recommended).
- If imports fail, verify the active interpreter is `varex_backend/venv`.
