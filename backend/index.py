"""
Vercel serverless function entry point.
Exposes the FastAPI app from main.py.
"""
from main import app

__all__ = ["app"]