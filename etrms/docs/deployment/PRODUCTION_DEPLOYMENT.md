# Production Deployment Guide for ETRMS

This guide provides step-by-step instructions for deploying the Enhanced Trading Risk Management System (ETRMS) to a production environment at riskmanage.xyz.

## Prerequisites

- A server with at least 4GB RAM and 2 CPU cores
- Docker and Docker Compose installed
- Domain name (riskmanage.xyz) with DNS configured to point to your server
- SSL certificate for your domain (we'll use Let's Encrypt)
- Basic understanding of Linux, Docker, and networking

## Deployment Steps

### 1. Clone the Repository

```bash
git clone https://github.com/your-organization/etrms.git
cd etrms
```

### 2. Set Up SSL Certificates

We'll use Let's Encrypt to obtain free SSL certificates:

```bash
# Install certbot
apt-get update
apt-get install -y certbot

# Obtain certificate
certbot certonly --standalone -d riskmanage.xyz -d www.riskmanage.xyz

# Create the SSL directory
mkdir -p etrms/docker/nginx/ssl

# Copy the certificates
cp /etc/letsencrypt/live/riskmanage.xyz/fullchain.pem etrms/docker/nginx/ssl/
cp /etc/letsencrypt/live/riskmanage.xyz/privkey.pem etrms/docker/nginx/ssl/
```

### 3. Configure Environment Variables

```bash
# Create the production environment file
cp etrms/docker/.env.prod.example etrms/docker/.env.prod

# Edit the environment variables with secure values
nano etrms/docker/.env.prod
```

Make sure to:
- Use a strong database password
- Set secure API and JWT secrets
- Add your exchange API keys if needed

### 4. Build and Start the Application

```bash
cd etrms/docker
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

### 5. Initialize the Database (First-time Setup)

```bash
# Enter the backend container
docker-compose -f docker-compose.prod.yml exec backend bash

# Inside the container, run database initialization
python scripts/initialize_db.py

# Exit the container
exit
```

### 6. Set Up Auto-Renewal for SSL Certificates

Create a script to renew certificates and update the containers:

```bash
cat > /etc/cron.monthly/renew-ssl-etrms << 'EOF'
#!/bin/bash

# Stop the containers
cd /path/to/etrms/docker
docker-compose -f docker-compose.prod.yml down

# Renew the certificate
certbot renew

# Copy the new certificates
cp /etc/letsencrypt/live/riskmanage.xyz/fullchain.pem /path/to/etrms/docker/nginx/ssl/
cp /etc/letsencrypt/live/riskmanage.xyz/privkey.pem /path/to/etrms/docker/nginx/ssl/

# Restart the containers
cd /path/to/etrms/docker
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
EOF

# Make the script executable
chmod +x /etc/cron.monthly/renew-ssl-etrms
```

### 7. Verify Deployment

Visit these URLs to verify that your application is working correctly:

- Frontend: https://riskmanage.xyz
- API: https://riskmanage.xyz/api/health

## Monitoring and Maintenance

### Logs

To view logs from your application:

```bash
cd etrms/docker
docker-compose -f docker-compose.prod.yml logs -f
```

For specific services:

```bash
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend
docker-compose -f docker-compose.prod.yml logs -f nginx
```

### Backups

Set up automated database backups:

```bash
cat > /etc/cron.daily/backup-etrms-db << 'EOF'
#!/bin/bash

TIMESTAMP=$(date +"%Y%m%d%H%M%S")
BACKUP_DIR="/path/to/backups"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Backup the database
cd /path/to/etrms/docker
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U etrms_user etrms > $BACKUP_DIR/etrms_$TIMESTAMP.sql

# Keep only the last 7 backups
ls -t $BACKUP_DIR/etrms_*.sql | tail -n +8 | xargs -I {} rm {}
EOF

# Make the script executable
chmod +x /etc/cron.daily/backup-etrms-db
```

### Updating the Application

To update the application with new code:

```bash
cd /path/to/etrms
git pull

cd docker
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

## Troubleshooting

### Application Not Accessible

Check if Docker containers are running:

```bash
docker-compose -f docker-compose.prod.yml ps
```

Verify Nginx configuration:

```bash
docker-compose -f docker-compose.prod.yml exec nginx nginx -t
```

### Database Connection Issues

Check database logs:

```bash
docker-compose -f docker-compose.prod.yml logs postgres
```

Verify environment variables:

```bash
docker-compose -f docker-compose.prod.yml exec backend env | grep DB_
```

## Security Considerations

1. **Regular Updates**: Keep the server and all software components updated
2. **Firewall**: Configure firewall to only allow necessary ports (80, 443)
3. **API Rate Limiting**: The Nginx configuration already includes rate limiting
4. **Access Control**: Implement IP restrictions for admin endpoints if needed
5. **Monitoring**: Set up alerts for unusual activity or resource usage

## Performance Optimization

1. **Scaling**: Adjust container resources based on load
2. **Caching**: Implement Redis caching for frequently accessed data
3. **Database Tuning**: Optimize PostgreSQL configuration for your workload
4. **CDN**: Consider using a CDN for static assets

## Contact and Support

For assistance with deployment issues, contact the development team at:
- Email: support@riskmanage.xyz
- Internal Issue Tracker: [Link to your issue tracker] 