"""Main FastAPI application with all routers configured."""
import os
import sys
import django
import logging

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django FIRST before any other imports
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "FundooMain.settings")
django.setup()

# NOW import FastAPI and routers after Django is ready
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_app.routers import collaborators
from fastapi_app.routers import auth
from common.api_response import build_api_response

# Setup logging
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Fundoo FastAPI",
    version="1.0.0",
    description="FastAPI module for FundooMain with collaborator endpoints",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this later for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return build_api_response("Service healthy", {"status": "ok"}, 200)


@app.get("/hello")
async def hello():
    return build_api_response("Hello from FastAPI", {"message": "Hello from FastAPI"}, 200)


# Include routers
app.include_router(collaborators.router)
app.include_router(auth.router)


# Global exception handler with logging
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {type(exc).__name__}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=build_api_response("Error", {"detail": f"Error: {str(exc)}"}, 500),
    )


# Standalone server runner
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        reload=True,
    )