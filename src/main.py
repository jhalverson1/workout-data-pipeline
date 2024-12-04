"""
Main Entry Point for Workout Tracking API Application

This module serves as the entry point for running the FastAPI application.
It configures and starts the Uvicorn server with the specified host and port
from the configuration.

The application can be started by running:
    python main.py

The API will be available at:
    http://{API_HOST}:{API_PORT}

Example:
    If API_HOST=0.0.0.0 and API_PORT=8000, the API will be available at:
    http://0.0.0.0:8000
"""

import uvicorn
from api import app
from config import Config

if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=True
    ) 