#!/bin/bash

# Enhanced Trading Risk Management System (ETRMS)
# Production Deployment Script

set -e

# Display banner
echo "==============================================="
echo "ETRMS Production Deployment Script"
echo "Target: riskmanage.xyz"
echo "==============================================="

# Check if script is run as root
if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root"
    exit 1
fi

# Check if domain is correct
read -p "Is your domain correctly set to riskmanage.xyz? (y/n): " confirm
if [[ "$confirm" != "y" ]]; then
    echo "Please set up your domain before proceeding."
    exit 1
fi

# Set working directory to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "Working directory: $PROJECT_ROOT"

# Create required directories
echo "Creating required directories..."
mkdir -p "$PROJECT_ROOT/docker/nginx/ssl"

# Check if SSL certificates exist
if [ ! -f "/etc/letsencrypt/live/riskmanage.xyz/fullchain.pem" ] || 
   [ ! -f "/etc/letsencrypt/live/riskmanage.xyz/privkey.pem" ]; then
    echo "SSL certificates not found. Setting up Let's Encrypt..."
    
    # Install certbot if not installed
    if ! command -v certbot &> /dev/null; then
        apt-get update
        apt-get install -y certbot
    fi
    
    # Stop any services that might be using port 80
    echo "Stopping any services that might be using port 80..."
    if [ -f "$PROJECT_ROOT/docker/docker-compose.prod.yml" ]; then
        cd "$PROJECT_ROOT/docker"
        docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
    fi
    
    # Get SSL certificate
    echo "Obtaining SSL certificate..."
    certbot certonly --standalone -d riskmanage.xyz -d www.riskmanage.xyz
    
    # Check if certificates were obtained successfully
    if [ ! -f "/etc/letsencrypt/live/riskmanage.xyz/fullchain.pem" ] || 
       [ ! -f "/etc/letsencrypt/live/riskmanage.xyz/privkey.pem" ]; then
        echo "Failed to obtain SSL certificates. Please check your domain configuration."
        exit 1
    fi
fi

# Copy SSL certificates
echo "Copying SSL certificates..."
cp /etc/letsencrypt/live/riskmanage.xyz/fullchain.pem "$PROJECT_ROOT/docker/nginx/ssl/"
cp /etc/letsencrypt/live/riskmanage.xyz/privkey.pem "$PROJECT_ROOT/docker/nginx/ssl/"

# Set up environment file
if [ ! -f "$PROJECT_ROOT/docker/.env.prod" ]; then
    echo "Setting up environment file..."
    cp "$PROJECT_ROOT/docker/.env.prod.example" "$PROJECT_ROOT/docker/.env.prod"
    
    # Generate random strings for secrets
    API_SECRET_KEY=$(openssl rand -hex 32)
    JWT_SECRET=$(openssl rand -hex 32)
    DB_PASSWORD=$(openssl rand -hex 16)
    
    # Update environment file with secure values
    sed -i "s/your_strong_password_here/$DB_PASSWORD/" "$PROJECT_ROOT/docker/.env.prod"
    sed -i "s/your_long_random_string_here/$API_SECRET_KEY/" "$PROJECT_ROOT/docker/.env.prod"
    sed -i "s/your_long_random_string_here/$JWT_SECRET/" "$PROJECT_ROOT/docker/.env.prod"
    
    echo "Environment file created with secure random values."
    echo "Please complete the exchange API keys in the .env.prod file if needed:"
    echo "$PROJECT_ROOT/docker/.env.prod"
fi

# Build and start the application
echo "Building and starting the application..."
cd "$PROJECT_ROOT/docker"
docker-compose -f docker-compose.prod.yml --env-file .env.prod down
docker-compose -f docker-compose.prod.yml --env-file .env.prod build
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Initialize the database
echo "Initializing the database (if needed)..."
echo "If this is a first-time setup, the script will initialize the database."
read -p "Is this a first-time setup? (y/n): " init_db
if [[ "$init_db" == "y" ]]; then
    docker-compose -f docker-compose.prod.yml exec backend python scripts/initialize_db.py
fi

# Create backup script
echo "Setting up database backup script..."
cat > /etc/cron.daily/backup-etrms-db << EOF
#!/bin/bash

TIMESTAMP=\$(date +"%Y%m%d%H%M%S")
BACKUP_DIR="$PROJECT_ROOT/backups"

# Create backup directory if it doesn't exist
mkdir -p \$BACKUP_DIR

# Backup the database
cd "$PROJECT_ROOT/docker"
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U etrms_user etrms > \$BACKUP_DIR/etrms_\$TIMESTAMP.sql

# Keep only the last 7 backups
ls -t \$BACKUP_DIR/etrms_*.sql | tail -n +8 | xargs -I {} rm {}
EOF

chmod +x /etc/cron.daily/backup-etrms-db

# Create SSL renewal script
echo "Setting up SSL certificate renewal script..."
cat > /etc/cron.monthly/renew-ssl-etrms << EOF
#!/bin/bash

# Stop the containers
cd "$PROJECT_ROOT/docker"
docker-compose -f docker-compose.prod.yml down

# Renew the certificate
certbot renew

# Copy the new certificates
cp /etc/letsencrypt/live/riskmanage.xyz/fullchain.pem "$PROJECT_ROOT/docker/nginx/ssl/"
cp /etc/letsencrypt/live/riskmanage.xyz/privkey.pem "$PROJECT_ROOT/docker/nginx/ssl/"

# Restart the containers
cd "$PROJECT_ROOT/docker"
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
EOF

chmod +x /etc/cron.monthly/renew-ssl-etrms

# Final message
echo "==============================================="
echo "ETRMS has been deployed to riskmanage.xyz!"
echo "==============================================="
echo "Frontend: https://riskmanage.xyz"
echo "API: https://riskmanage.xyz/api"
echo ""
echo "To view logs: docker-compose -f $PROJECT_ROOT/docker/docker-compose.prod.yml logs -f"
echo "Database backups will be stored in: $PROJECT_ROOT/backups"
echo ""
echo "If you need to make manual changes to the environment, edit:"
echo "$PROJECT_ROOT/docker/.env.prod"
echo ""
echo "For help, refer to the deployment guide:"
echo "$PROJECT_ROOT/docs/deployment/PRODUCTION_DEPLOYMENT.md"
echo "===============================================" 