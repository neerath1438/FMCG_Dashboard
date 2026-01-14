#!/bin/bash

# FMCG Dashboard - Automated Deployment Script
# Replace these variables with your actual values

DOMAIN="yourdomain.com"
API_DOMAIN="api.yourdomain.com"
EMAIL="your-email@example.com"
PROJECT_PATH="~/projects/FMCG_Dashboard"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}FMCG Dashboard Deployment Script${NC}"
echo -e "${GREEN}========================================${NC}"

# Function to print status
print_status() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Step 1: Pull latest code
print_status "Pulling latest code..."
cd $PROJECT_PATH || exit 1
git pull origin main
if [ $? -eq 0 ]; then
    print_success "Code updated"
else
    print_error "Failed to pull code"
    exit 1
fi

# Step 2: Stop Docker containers
print_status "Stopping Docker containers..."
docker compose down
print_success "Containers stopped"

# Step 3: Get SSL certificates
print_status "Getting SSL certificate for frontend..."
sudo certbot certonly --standalone \
  -d $DOMAIN \
  -d www.$DOMAIN \
  --non-interactive \
  --agree-tos \
  --email $EMAIL

if [ $? -eq 0 ]; then
    print_success "Frontend SSL certificate obtained"
else
    print_error "Failed to get frontend SSL certificate"
    exit 1
fi

print_status "Getting SSL certificate for backend..."
sudo certbot certonly --standalone \
  -d $API_DOMAIN \
  --non-interactive \
  --agree-tos \
  --email $EMAIL

if [ $? -eq 0 ]; then
    print_success "Backend SSL certificate obtained"
else
    print_error "Failed to get backend SSL certificate"
    exit 1
fi

# Step 4: Set permissions
print_status "Setting certificate permissions..."
sudo chmod -R 755 /etc/letsencrypt/live/
sudo chmod -R 755 /etc/letsencrypt/archive/
print_success "Permissions set"

# Step 5: Update nginx config
print_status "Updating nginx configuration..."
sudo cp $PROJECT_PATH/nginx/fmcg-retail.conf /etc/nginx/conf.d/$DOMAIN.conf

# Test nginx config
sudo nginx -t
if [ $? -eq 0 ]; then
    print_success "Nginx config valid"
    sudo systemctl reload nginx
    print_success "Nginx reloaded"
else
    print_error "Nginx config invalid"
    exit 1
fi

# Step 6: Rebuild Docker images
print_status "Rebuilding Docker images..."
cd $PROJECT_PATH
docker compose build
if [ $? -eq 0 ]; then
    print_success "Images built"
else
    print_error "Failed to build images"
    exit 1
fi

# Step 7: Start containers
print_status "Starting Docker containers..."
docker compose up -d
if [ $? -eq 0 ]; then
    print_success "Containers started"
else
    print_error "Failed to start containers"
    exit 1
fi

# Step 8: Wait for services to start
print_status "Waiting for services to start..."
sleep 10

# Step 9: Verify deployment
print_status "Verifying deployment..."

# Check containers
echo ""
echo "Container Status:"
docker compose ps

# Test frontend
echo ""
print_status "Testing frontend..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN)
if [ "$FRONTEND_STATUS" == "200" ]; then
    print_success "Frontend is accessible (HTTP $FRONTEND_STATUS)"
else
    print_error "Frontend returned HTTP $FRONTEND_STATUS"
fi

# Test backend
echo ""
print_status "Testing backend..."
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -k https://$API_DOMAIN/dashboard/summary)
if [ "$BACKEND_STATUS" == "200" ]; then
    print_success "Backend API is accessible (HTTP $BACKEND_STATUS)"
else
    print_error "Backend returned HTTP $BACKEND_STATUS"
fi

# Final summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Frontend:  https://$DOMAIN"
echo "Backend:   https://$API_DOMAIN"
echo "Login:     rosini.alexander@metora.co / Roshini@123"
echo ""
echo "Check logs: docker compose logs -f"
echo ""
