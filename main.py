"""
Entry point – run the FastAPI server.
Usage:  python main.py
        uvicorn main:app --reload
"""
import uvicorn
from backend.api.app import app  # noqa: F401  (re-export for uvicorn)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(__import__("os").getenv("PORT", 8000)),
        reload=True,
    )
