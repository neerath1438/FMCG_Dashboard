#!/bin/bash

# FMCG Dashboard SSL Setup Script (Manual DNS Challenge)
# This script uses DNS challenge method to avoid port 80 conflicts
# Run this on your server: 20.0.161.242

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
FRONTEND_DOMAIN="retail.wersel.co.uk"
BACKEND_DOMAIN="retail-api.wersel.co.uk"
EMAIL="vishnu.t@wersel.io"
NGINX_CONF_PATH="/etc/nginx/sites-available/fmcg-retail.conf"
NGINX_ENABLED_PATH="/etc/nginx/sites-enabled/fmcg-retail.conf"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}FMCG Dashboard SSL Setup (DNS Challenge)${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}This script uses DNS challenge method${NC}"
echo -e "${YELLOW}No need to stop your production application!${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root or with sudo${NC}"
    exit 1
fi

# Step 1: Install Certbot
echo -e "${YELLOW}Step 1: Installing Certbot...${NC}"
apt update -qq
apt install -y certbot > /dev/null 2>&1
echo -e "${GREEN}✓ Certbot installed${NC}"
echo ""

# Step 2: Generate SSL certificate for Frontend
echo -e "${YELLOW}Step 2: Generating SSL certificate for $FRONTEND_DOMAIN...${NC}"
echo ""

if [ ! -d "/etc/letsencrypt/live/$FRONTEND_DOMAIN" ]; then
    echo -e "${BLUE}Starting certificate request...${NC}"
    echo ""
    
    certbot certonly --manual \
        --preferred-challenges dns \
        -d $FRONTEND_DOMAIN \
        -d www.$FRONTEND_DOMAIN \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email
    
    echo ""
    echo -e "${GREEN}✓ Frontend certificate obtained${NC}"
else
    echo -e "${GREEN}✓ Frontend certificate already exists${NC}"
fi

echo ""

# Step 3: Generate SSL certificate for Backend
echo -e "${YELLOW}Step 3: Generating SSL certificate for $BACKEND_DOMAIN...${NC}"
echo ""

if [ ! -d "/etc/letsencrypt/live/$BACKEND_DOMAIN" ]; then
    echo -e "${BLUE}Starting certificate request...${NC}"
    echo ""
    
    certbot certonly --manual \
        --preferred-challenges dns \
        -d $BACKEND_DOMAIN \
        -d www.$BACKEND_DOMAIN \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email
    
    echo ""
    echo -e "${GREEN}✓ Backend certificate obtained${NC}"
else
    echo -e "${GREEN}✓ Backend certificate already exists${NC}"
fi

echo ""

# Step 4: Deploy Nginx configuration
echo -e "${YELLOW}Step 4: Deploying Nginx configuration...${NC}"

# Check if config file exists
if [ -f "./nginx/fmcg-retail.conf" ]; then
    cp ./nginx/fmcg-retail.conf $NGINX_CONF_PATH
    echo -e "${GREEN}✓ Nginx config copied${NC}"
elif [ -f "./fmcg-retail.conf" ]; then
    cp ./fmcg-retail.conf $NGINX_CONF_PATH
    echo -e "${GREEN}✓ Nginx config copied${NC}"
else
    echo -e "${RED}✗ Nginx config file not found${NC}"
    exit 1
fi

# Enable the site
ln -sf $NGINX_CONF_PATH $NGINX_ENABLED_PATH
echo -e "${GREEN}✓ Nginx site enabled${NC}"

echo ""

# Step 5: Test Nginx configuration
echo -e "${YELLOW}Step 5: Testing Nginx configuration...${NC}"
if nginx -t; then
    echo -e "${GREEN}✓ Nginx configuration is valid${NC}"
else
    echo -e "${RED}✗ Nginx configuration has errors${NC}"
    exit 1
fi

echo ""

# Step 6: Reload Nginx
echo -e "${YELLOW}Step 6: Reloading Nginx...${NC}"
systemctl reload nginx
echo -e "${GREEN}✓ Nginx reloaded${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}SSL Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Frontend URL: ${GREEN}https://$FRONTEND_DOMAIN${NC}"
echo -e "Backend URL:  ${GREEN}https://$BACKEND_DOMAIN${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Test the frontend: https://$FRONTEND_DOMAIN"
echo "2. Rebuild Docker containers: docker-compose down && docker-compose up -d --build"
echo ""
