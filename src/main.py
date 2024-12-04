"""
Main entry point for the workout tracking API application.
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