"""
Enhanced Trading Risk Management System - Simplified App

This module provides a simplified FastAPI application for testing.
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import jwt

# Create FastAPI application
app = FastAPI(
    title="Enhanced Trading Risk Management System API",
    description="API for the Enhanced Trading Risk Management System",
    version="0.1.0",
)

# Add CORS middleware
origins = [
    "http://localhost",
    "http://localhost:3000",  # React development server
    "http://localhost:3002",  # Another React development server
    "http://localhost:8000",  # FastAPI development server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication settings
SECRET_KEY = "development_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

# Fake user database
fake_users_db = {
    "admin": {
        "username": "admin",
        "email": "admin@example.com",
        "full_name": "Admin User",
        "disabled": False,
        "hashed_password": "admin"  # In a real app, this would be hashed
    }
}

# Authentication functions
def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if password != user.hashed_password:  # In a real app, we would verify the hash
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# API routes
@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to the Enhanced Trading Risk Management System API",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

@app.get("/test", response_class=HTMLResponse)
async def test_page():
    """Test page endpoint."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ETRMS Test Page</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                line-height: 1.6;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
                border-radius: 5px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
            }
            .card {
                background-color: white;
                padding: 15px;
                margin-bottom: 15px;
                border-radius: 5px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            .success {
                color: green;
                font-weight: bold;
            }
            button {
                background-color: #4CAF50;
                color: white;
                padding: 10px 15px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
            }
            button:hover {
                background-color: #45a049;
            }
            pre {
                background-color: #f8f8f8;
                padding: 10px;
                border-radius: 4px;
                overflow-x: auto;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>ETRMS Test Page</h1>
            <p>This page is used to test the connection to the backend API.</p>
            
            <div class="card">
                <h2>Backend Status</h2>
                <p class="success">✅ Backend is running and accessible!</p>
                <p>You're seeing this page, which means the backend server is working correctly.</p>
            </div>
            
            <div class="card">
                <h2>Authentication Test</h2>
                <p>Test authentication with the following credentials:</p>
                <pre>Username: admin
Password: admin</pre>
                <button onclick="testAuth()">Test Authentication</button>
                <div id="auth-result" style="margin-top: 10px;"></div>
            </div>
            
            <div class="card">
                <h2>API Endpoints</h2>
                <ul>
                    <li><a href="/" target="_blank">Root Endpoint</a></li>
                    <li><a href="/docs" target="_blank">API Documentation</a></li>
                    <li><a href="/api/v1/exchanges" target="_blank">Available Exchanges</a></li>
                </ul>
            </div>
        </div>
        
        <script>
            async function testAuth() {
                const resultDiv = document.getElementById('auth-result');
                resultDiv.innerHTML = 'Testing authentication...';
                
                try {
                    const formData = new URLSearchParams();
                    formData.append('username', 'admin');
                    formData.append('password', 'admin');
                    
                    const response = await fetch('/token', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                        },
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        resultDiv.innerHTML = `
                            <p class="success">✅ Authentication successful!</p>
                            <p>Token: ${data.access_token.substring(0, 20)}...</p>
                        `;
                    } else {
                        resultDiv.innerHTML = `
                            <p style="color: red;">❌ Authentication failed!</p>
                            <p>Error: ${data.detail || 'Unknown error'}</p>
                        `;
                    }
                } catch (error) {
                    resultDiv.innerHTML = `
                        <p style="color: red;">❌ Error testing authentication!</p>
                        <p>Error: ${error.message}</p>
                    `;
                }
            }
        </script>
    </body>
    </html>
    """
    return html_content

@app.get("/api/v1/exchanges")
async def get_exchanges():
    """Get available exchanges."""
    return {
        "status": "success",
        "data": ["binance", "hyperliquid", "bybit"]
    }

@app.get("/api/v1/exchanges/{exchange}/symbols")
async def get_symbols(exchange: str):
    """Get available symbols for an exchange."""
    symbols = {
        "binance": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT"],
        "hyperliquid": ["BTCUSD", "ETHUSD", "SOLUSD", "BNBUSD", "ADAUSD"],
        "bybit": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT"]
    }
    
    return {
        "status": "success",
        "data": symbols.get(exchange, [])
    }

@app.get("/api/v1/assistant/setups")
async def get_setups():
    """Get trading setups."""
    return {
        "status": "success",
        "data": [
            {
                "id": "setup_1",
                "exchange": "binance",
                "symbol": "BTCUSDT",
                "setup_type": "breakout",
                "timeframe": "1h",
                "quality": 0.85,
                "direction": "long",
                "detected_at": "2023-05-01T12:34:56Z",
                "key_levels": {
                    "entry": 42000,
                    "stop_loss": 41200,
                    "targets": [43500, 45000]
                },
                "indicators": {
                    "rsi": 68,
                    "volume_change": 1.45,
                    "support_level": 41200
                },
                "description": "Bullish breakout from ascending triangle pattern with increasing volume."
            },
            {
                "id": "setup_2",
                "exchange": "binance",
                "symbol": "ETHUSDT",
                "setup_type": "trend_continuation",
                "timeframe": "1h",
                "quality": 0.78,
                "direction": "long",
                "detected_at": "2023-05-01T14:56:23Z",
                "key_levels": {
                    "entry": 2850,
                    "stop_loss": 2780,
                    "targets": [2950, 3050]
                },
                "indicators": {
                    "rsi": 62,
                    "volume_change": 1.2,
                    "support_level": 2780
                },
                "description": "Bullish trend continuation after pullback to 20 EMA with bullish engulfing pattern."
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "simple_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    ) 