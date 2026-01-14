#!/bin/bash

# FMCG Dashboard SSL Setup Script
# This script automates the SSL certificate generation and Nginx configuration
# Run this on your server: 20.0.161.242

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
FRONTEND_DOMAIN="retail.wersel.co.uk"
BACKEND_DOMAIN="retail-api.wersel.co.uk"
EMAIL="your-email@example.com"  # CHANGE THIS!
NGINX_CONF_PATH="/etc/nginx/sites-available/fmcg-retail.conf"
NGINX_ENABLED_PATH="/etc/nginx/sites-enabled/fmcg-retail.conf"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}FMCG Dashboard SSL Setup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root or with sudo${NC}"
    exit 1
fi

# Step 1: Check DNS resolution
echo -e "${YELLOW}Step 1: Checking DNS resolution...${NC}"
if nslookup $FRONTEND_DOMAIN | grep -q "20.0.161.242"; then
    echo -e "${GREEN}✓ Frontend domain DNS is correct${NC}"
else
    echo -e "${RED}✗ Frontend domain DNS not pointing to 20.0.161.242${NC}"
    echo -e "${YELLOW}Please update your DNS records and wait for propagation${NC}"
    exit 1
fi

if nslookup $BACKEND_DOMAIN | grep -q "20.0.161.242"; then
    echo -e "${GREEN}✓ Backend domain DNS is correct${NC}"
else
    echo -e "${RED}✗ Backend domain DNS not pointing to 20.0.161.242${NC}"
    echo -e "${YELLOW}Please update your DNS records and wait for propagation${NC}"
    exit 1
fi

echo ""

# Step 2: Install Certbot
echo -e "${YELLOW}Step 2: Installing Certbot...${NC}"
apt update -qq
apt install -y certbot python3-certbot-nginx > /dev/null 2>&1
echo -e "${GREEN}✓ Certbot installed${NC}"
echo ""

# Step 3: Stop Nginx temporarily (to avoid port conflicts)
echo -e "${YELLOW}Step 3: Stopping Nginx temporarily...${NC}"
systemctl stop nginx || true
echo -e "${GREEN}✓ Nginx stopped${NC}"
echo ""

# Step 4: Obtain SSL certificates
echo -e "${YELLOW}Step 4: Obtaining SSL certificates...${NC}"

# Frontend certificate
if [ ! -d "/etc/letsencrypt/live/$FRONTEND_DOMAIN" ]; then
    echo -e "${YELLOW}Obtaining certificate for $FRONTEND_DOMAIN...${NC}"
    certbot certonly --standalone \
        -d $FRONTEND_DOMAIN \
        -d www.$FRONTEND_DOMAIN \
        --non-interactive \
        --agree-tos \
        --email $EMAIL \
        --preferred-challenges http
    echo -e "${GREEN}✓ Frontend certificate obtained${NC}"
else
    echo -e "${GREEN}✓ Frontend certificate already exists${NC}"
fi

# Backend certificate
if [ ! -d "/etc/letsencrypt/live/$BACKEND_DOMAIN" ]; then
    echo -e "${YELLOW}Obtaining certificate for $BACKEND_DOMAIN...${NC}"
    certbot certonly --standalone \
        -d $BACKEND_DOMAIN \
        -d www.$BACKEND_DOMAIN \
        --non-interactive \
        --agree-tos \
        --email $EMAIL \
        --preferred-challenges http
    echo -e "${GREEN}✓ Backend certificate obtained${NC}"
else
    echo -e "${GREEN}✓ Backend certificate already exists${NC}"
fi

echo ""

# Step 5: Deploy Nginx configuration
echo -e "${YELLOW}Step 5: Deploying Nginx configuration...${NC}"

# Check if config file exists in current directory
if [ -f "./fmcg-retail.conf" ]; then
    cp ./fmcg-retail.conf $NGINX_CONF_PATH
    echo -e "${GREEN}✓ Nginx config copied from current directory${NC}"
elif [ -f "/tmp/fmcg-retail.conf" ]; then
    cp /tmp/fmcg-retail.conf $NGINX_CONF_PATH
    echo -e "${GREEN}✓ Nginx config copied from /tmp${NC}"
else
    echo -e "${RED}✗ Nginx config file not found${NC}"
    echo -e "${YELLOW}Please upload fmcg-retail.conf to current directory or /tmp${NC}"
    exit 1
fi

# Create symbolic link
ln -sf $NGINX_CONF_PATH $NGINX_ENABLED_PATH
echo -e "${GREEN}✓ Nginx site enabled${NC}"

# Remove default site
rm -f /etc/nginx/sites-enabled/default
echo -e "${GREEN}✓ Default site removed${NC}"

echo ""

# Step 6: Test Nginx configuration
echo -e "${YELLOW}Step 6: Testing Nginx configuration...${NC}"
if nginx -t; then
    echo -e "${GREEN}✓ Nginx configuration is valid${NC}"
else
    echo -e "${RED}✗ Nginx configuration has errors${NC}"
    exit 1
fi

echo ""

# Step 7: Start Nginx
echo -e "${YELLOW}Step 7: Starting Nginx...${NC}"
systemctl start nginx
systemctl enable nginx
echo -e "${GREEN}✓ Nginx started and enabled${NC}"

echo ""

# Step 8: Configure firewall
echo -e "${YELLOW}Step 8: Configuring firewall...${NC}"
if command -v ufw &> /dev/null; then
    ufw allow 80/tcp > /dev/null 2>&1
    ufw allow 443/tcp > /dev/null 2>&1
    echo -e "${GREEN}✓ Firewall rules added${NC}"
else
    echo -e "${YELLOW}⚠ UFW not found, skipping firewall configuration${NC}"
fi

echo ""

# Step 9: Verify Docker containers
echo -e "${YELLOW}Step 9: Checking Docker containers...${NC}"
if docker ps | grep -q "fmcg_frontend"; then
    echo -e "${GREEN}✓ Frontend container is running${NC}"
else
    echo -e "${RED}✗ Frontend container is not running${NC}"
    echo -e "${YELLOW}Please start Docker containers: docker-compose up -d${NC}"
fi

if docker ps | grep -q "fmcg_backend"; then
    echo -e "${GREEN}✓ Backend container is running${NC}"
else
    echo -e "${RED}✗ Backend container is not running${NC}"
    echo -e "${YELLOW}Please start Docker containers: docker-compose up -d${NC}"
fi

echo ""

# Step 10: Test SSL endpoints
echo -e "${YELLOW}Step 10: Testing SSL endpoints...${NC}"
sleep 2  # Wait for Nginx to fully start

if curl -s -o /dev/null -w "%{http_code}" https://$FRONTEND_DOMAIN | grep -q "200\|301\|302"; then
    echo -e "${GREEN}✓ Frontend HTTPS is working${NC}"
else
    echo -e "${RED}✗ Frontend HTTPS is not responding${NC}"
fi

if curl -s -o /dev/null -w "%{http_code}" https://$BACKEND_DOMAIN/health | grep -q "200"; then
    echo -e "${GREEN}✓ Backend HTTPS is working${NC}"
else
    echo -e "${YELLOW}⚠ Backend HTTPS health check failed (this may be normal if /health endpoint doesn't exist)${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}SSL Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Frontend URL: ${GREEN}https://$FRONTEND_DOMAIN${NC}"
echo -e "Backend URL:  ${GREEN}https://$BACKEND_DOMAIN${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Test the frontend in your browser: https://$FRONTEND_DOMAIN"
echo "2. Check SSL certificate: https://www.ssllabs.com/ssltest/"
echo "3. Monitor logs: sudo tail -f /var/log/nginx/error.log"
echo ""
echo -e "${YELLOW}Auto-renewal:${NC}"
echo "Certbot will automatically renew certificates before expiry."
echo "Test renewal: sudo certbot renew --dry-run"
echo ""
