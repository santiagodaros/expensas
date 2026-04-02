"""Entry point PyInstaller para Gestor de Consorcios API."""
import sys
import os

if getattr(sys, "frozen", False):
    _root = os.path.dirname(sys.executable)
else:
    _root = os.path.dirname(os.path.abspath(__file__))

if _root not in sys.path:
    sys.path.insert(0, _root)

import uvicorn
from api.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")