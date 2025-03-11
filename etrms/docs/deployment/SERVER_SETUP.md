# Server Setup Guide for ETRMS

This guide provides instructions for setting up a new server to host the Enhanced Trading Risk Management System (ETRMS) at riskmanage.xyz.

## Server Requirements

- Ubuntu 22.04 LTS (recommended)
- Minimum 4GB RAM, 2 CPU cores, 50GB SSD storage
- Public IP address
- Root access or sudo privileges

## Initial Server Setup

### 1. Update System

```bash
apt update && apt upgrade -y
```

### 2. Install Required Packages

```bash
apt install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    ufw \
    fail2ban
```

### 3. Set Up Firewall

```bash
# Configure UFW
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow http
ufw allow https
ufw enable
```

### 4. Configure Fail2ban

```bash
# Basic fail2ban configuration
cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
systemctl enable fail2ban
systemctl start fail2ban
```

### 5. Install Docker and Docker Compose

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
mkdir -p ~/.docker/cli-plugins/
curl -SL https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-linux-x86_64 -o ~/.docker/cli-plugins/docker-compose
chmod +x ~/.docker/cli-plugins/docker-compose

# Verify installation
docker --version
docker compose version
```

### 6. Configure DNS for riskmanage.xyz

1. Log in to your domain registrar (where you purchased riskmanage.xyz)
2. Add the following DNS records:
   - Type: A, Name: @, Value: [Your Server IP]
   - Type: A, Name: www, Value: [Your Server IP]
   - Type: CNAME, Name: api, Value: riskmanage.xyz
   - Type: CNAME, Name: docs, Value: riskmanage.xyz

3. Wait for DNS propagation (can take up to 24-48 hours)

## Install ETRMS

### 1. Clone the Repository

```bash
git clone https://github.com/your-organization/etrms.git
cd etrms
```

### 2. Run the Deployment Script

```bash
./scripts/deploy_production.sh
```

Follow the prompts in the script to complete the installation.

## Server Hardening (Optional but Recommended)

### 1. Disable Password Authentication for SSH

Edit the SSH configuration:

```bash
nano /etc/ssh/sshd_config
```

Update the following settings:

```
PasswordAuthentication no
PubkeyAuthentication yes
PermitRootLogin prohibit-password
```

Restart SSH:

```bash
systemctl restart sshd
```

### 2. Set Up Automatic Security Updates

```bash
apt install -y unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades
```

### 3. Enable Log Monitoring

```bash
apt install -y logwatch
nano /etc/cron.daily/00logwatch
```

Add:

```
/usr/sbin/logwatch --output mail --mailto your-email@example.com --detail high
```

## Monitoring Setup

### 1. Install Basic Monitoring

```bash
apt install -y htop iotop nethogs
```

### 2. Set Up Monitoring Stack (Optional)

For advanced monitoring, consider installing:

- Prometheus for metrics collection
- Grafana for metrics visualization
- Alert Manager for alerts

## Backup Strategy

The deployment script sets up daily database backups. Additionally, consider:

1. Setting up external backups to cloud storage

```bash
# Install AWS CLI for S3 backups
apt install -y awscli

# Configure AWS credentials
aws configure
```

2. Create a backup script for external storage:

```bash
cat > /etc/cron.weekly/etrms-external-backup << 'EOF'
#!/bin/bash

TIMESTAMP=$(date +"%Y%m%d%H%M%S")
BACKUP_DIR="/path/to/etrms/backups"
S3_BUCKET="your-bucket-name"

# Compress the latest backup
tar -czf $BACKUP_DIR/etrms_backup_$TIMESTAMP.tar.gz $BACKUP_DIR/etrms_*.sql

# Upload to S3
aws s3 cp $BACKUP_DIR/etrms_backup_$TIMESTAMP.tar.gz s3://$S3_BUCKET/

# Clean up old compressed backups
find $BACKUP_DIR -name "etrms_backup_*.tar.gz" -type f -mtime +7 -delete
EOF

chmod +x /etc/cron.weekly/etrms-external-backup
```

## Troubleshooting

If you encounter issues during setup, check:

1. DNS configuration using `nslookup riskmanage.xyz`
2. Firewall settings using `ufw status`
3. Docker service using `systemctl status docker`
4. Docker logs using `docker compose logs`

## Regular Maintenance Tasks

1. Monitor disk space:
   ```bash
   df -h
   ```

2. Check system load:
   ```bash
   htop
   ```

3. Prune Docker resources periodically:
   ```bash
   docker system prune -a
   ```

4. Check backup integrity:
   ```bash
   # Test restoring a backup to verify integrity
   cd /path/to/etrms/docker
   docker-compose -f docker-compose.prod.yml exec postgres psql -U etrms_user -d etrms_test -c "SELECT 1"
   ``` 