#!/bin/bash

# FMCG Dashboard SSL Setup - Final Solution
# Uses existing web server on port 80 for SSL verification
# No downtime required!

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

FRONTEND_DOMAIN="retail.wersel.co.uk"
BACKEND_DOMAIN="retail-api.wersel.co.uk"
EMAIL="vishnu.t@wersel.io"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}FMCG SSL Setup - No Downtime Method${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root or with sudo${NC}"
    exit 1
fi

# Step 1: Create webroot directory for SSL verification
echo -e "${YELLOW}Step 1: Setting up webroot for SSL verification...${NC}"

# Find the Docker container serving port 80
CONTAINER_ID=$(docker ps --filter "publish=80" --format "{{.ID}}" | head -1)

if [ -z "$CONTAINER_ID" ]; then
    echo -e "${RED}No Docker container found on port 80${NC}"
    exit 1
fi

echo "Found container: $CONTAINER_ID"

# Create .well-known directory inside the container
docker exec $CONTAINER_ID mkdir -p /usr/share/nginx/html/.well-known/acme-challenge || true
docker exec $CONTAINER_ID chmod -R 755 /usr/share/nginx/html/.well-known || true

# Also create on host (in case container uses volume mount)
mkdir -p /var/www/html/.well-known/acme-challenge
chmod -R 755 /var/www/html

echo -e "${GREEN}✓ Webroot configured${NC}"
echo ""

# Step 2: Generate SSL certificate using webroot
echo -e "${YELLOW}Step 2: Generating SSL certificates...${NC}"

# Frontend certificate
if [ ! -d "/etc/letsencrypt/live/$FRONTEND_DOMAIN" ]; then
    echo "Generating certificate for $FRONTEND_DOMAIN..."
    
    certbot certonly --webroot \
        -w /var/www/html \
        -d $FRONTEND_DOMAIN \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        --non-interactive || {
            echo -e "${YELLOW}Webroot method failed, trying with container path...${NC}"
            
            # Try with container's nginx path
            docker exec $CONTAINER_ID mkdir -p /app/.well-known/acme-challenge
            certbot certonly --webroot \
                -w /app \
                -d $FRONTEND_DOMAIN \
                --email $EMAIL \
                --agree-tos \
                --no-eff-email \
                --non-interactive
        }
    
    echo -e "${GREEN}✓ Frontend certificate generated${NC}"
else
    echo -e "${GREEN}✓ Frontend certificate already exists${NC}"
fi

# Backend certificate
if [ ! -d "/etc/letsencrypt/live/$BACKEND_DOMAIN" ]; then
    echo "Generating certificate for $BACKEND_DOMAIN..."
    
    certbot certonly --webroot \
        -w /var/www/html \
        -d $BACKEND_DOMAIN \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        --non-interactive
    
    echo -e "${GREEN}✓ Backend certificate generated${NC}"
else
    echo -e "${GREEN}✓ Backend certificate already exists${NC}"
fi

echo ""

# Step 3: Deploy Nginx configuration
echo -e "${YELLOW}Step 3: Deploying Nginx configuration...${NC}"

if [ -f "./nginx/fmcg-retail.conf" ]; then
    cp ./nginx/fmcg-retail.conf /etc/nginx/sites-available/
    ln -sf /etc/nginx/sites-available/fmcg-retail.conf /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    echo -e "${GREEN}✓ Nginx config deployed${NC}"
else
    echo -e "${RED}✗ Nginx config not found${NC}"
    exit 1
fi

echo ""

# Step 4: Test and reload Nginx
echo -e "${YELLOW}Step 4: Testing Nginx configuration...${NC}"
if nginx -t; then
    echo -e "${GREEN}✓ Nginx config valid${NC}"
    systemctl reload nginx || systemctl start nginx
    echo -e "${GREEN}✓ Nginx reloaded${NC}"
else
    echo -e "${RED}✗ Nginx config has errors${NC}"
    exit 1
fi

echo ""

# Step 5: Rebuild Docker containers
echo -e "${YELLOW}Step 5: Rebuilding Docker containers...${NC}"
cd ~/fmcg-server/FMCG_Dashboard
docker-compose up -d --build
echo -e "${GREEN}✓ Docker containers rebuilt${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}SSL Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Frontend: ${GREEN}https://$FRONTEND_DOMAIN${NC}"
echo -e "Backend:  ${GREEN}https://$BACKEND_DOMAIN${NC}"
echo ""
echo "Test with: curl -I https://$FRONTEND_DOMAIN"
echo ""
