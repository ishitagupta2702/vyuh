from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.schema import graphql_app
from app.core.config import settings
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Vyuh API",
    description="Backend API for Vyuh - AI-Powered Publishing Platform",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GraphQL endpoint
app.include_router(graphql_app, prefix="/graphql")

@app.get("/")
async def root():
    return {
        "message": "Welcome to Vyuh API",
        "docs": "/docs",
        "graphql": "/graphql",
        "version": "0.1.0"
    }
