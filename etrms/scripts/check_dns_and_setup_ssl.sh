#!/bin/bash

# Script to check DNS propagation and set up SSL certificates once propagation is complete
DOMAIN="riskmanage.xyz"
EXPECTED_IP="69.30.85.130"
CHECK_INTERVAL=600  # Check every 10 minutes

echo "Starting DNS propagation check for $DOMAIN..."
echo "Waiting for DNS to resolve to $EXPECTED_IP..."
echo "Press Ctrl+C to exit the script at any time."
echo "---------------------------------------------"

while true; do
    current_time=$(date +"%Y-%m-%d %H:%M:%S")
    resolved_ip=$(host $DOMAIN | grep "has address" | awk '{print $4}')
    
    if [ "$resolved_ip" = "$EXPECTED_IP" ]; then
        echo "[$current_time] Success! DNS has propagated correctly: $DOMAIN resolves to $EXPECTED_IP"
        echo "Setting up SSL certificates with Let's Encrypt..."
        
        # Run Certbot to obtain SSL certificates and configure Nginx
        certbot --nginx -d $DOMAIN -d www.$DOMAIN
        
        if [ $? -eq 0 ]; then
            echo "SSL certificates have been successfully installed!"
            echo "Your website is now accessible via HTTPS: https://$DOMAIN"
            
            # Verify Nginx configuration
            nginx -t
            
            # Reload Nginx to apply changes if configuration test passes
            if [ $? -eq 0 ]; then
                service nginx reload
                echo "Nginx configuration has been reloaded."
            fi
            
            exit 0
        else
            echo "Error occurred during SSL certificate installation."
            echo "Please run 'certbot --nginx -d $DOMAIN -d www.$DOMAIN' manually."
            exit 1
        fi
    else
        echo "[$current_time] DNS still propagating: $DOMAIN currently resolves to $resolved_ip (waiting for $EXPECTED_IP)"
        echo "Checking again in $(($CHECK_INTERVAL / 60)) minutes..."
        sleep $CHECK_INTERVAL
    fi
done 