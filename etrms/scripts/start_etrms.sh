#!/bin/bash

# ETRMS Startup Script

echo "Starting ETRMS Application..."

# Set environment variables
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=etrms
export DB_USER=etrms_user
export DB_PASSWORD=etrms_password
export API_SECRET_KEY=your_api_secret_key_here
export JWT_SECRET=your_jwt_secret_here
export JWT_ALGORITHM=HS256
export JWT_EXPIRATION_MINUTES=1440
export BINANCE_API_KEY=nAi2Bs6HypxUuStvGYoqkhSZXfojZdBC9ZMsyHjNFCFvcJp3U9JzCzrBqPsjxuQz
export BINANCE_API_SECRET=ICUI7mSWnpq3zmHnXAWafjkaUuZkxc2WzadmkLGaJ02Zg8Q4EGvcMeBW9GIDGgq9
export BINANCE_TESTNET=false
export HYPERLIQUID_API_KEY=0x47671eb079c1a8ccad590ff08446b328e237e2ef
export HYPERLIQUID_API_SECRET=0xb49672dbe59d483f285aeea81d59c1406c66719a0cec4e6a6ee51cecedb48040
export HYPERLIQUID_WALLET_ADDRESS=0x0527D05471a11E58232fCe84711AaBDAc2753e2f
export API_BASE_URL=http://riskmanage.xyz/api
export FRONTEND_URL=http://riskmanage.xyz
export PYTHONPATH=/root/Discipline/etrms/backend

# Start Nginx
echo "Starting Nginx..."
service nginx restart

# Start the backend in the background
echo "Starting Backend Service..."
cd /root/Discipline/etrms
source venv/bin/activate
cd backend
uvicorn app:app --host 0.0.0.0 --port 8000 >> /root/Discipline/etrms/backend/etrms.log 2>&1 &

echo "ETRMS Application Started"
echo "Frontend: http://riskmanage.xyz"
echo "API: http://riskmanage.xyz/api" 