import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from etrms.backend.api.routes import auth, accounts, risk, websocket, backtest
from etrms.backend.db.database import close_client
from etrms.backend.utils.error_handler import setup_exception_handlers

# Create FastAPI app
app = FastAPI(
    title="Enhanced Trading Risk Management System API",
    description="API for the Enhanced Trading Risk Management System",
    version="0.1.0"
)

# Configure CORS
origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    os.environ.get("FRONTEND_URL", "http://localhost:3000")
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up exception handlers
setup_exception_handlers(app)

# Include routers
app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(risk.router)
app.include_router(websocket.router)
app.include_router(backtest.router)

@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    # Initialize any resources here
    pass

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    # Close database connection
    close_client()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to the Enhanced Trading Risk Management System API",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    } 