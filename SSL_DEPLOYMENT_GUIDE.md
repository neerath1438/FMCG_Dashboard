# SSL Deployment Guide for FMCG Dashboard

This guide will help you set up SSL certificates and configure Nginx to serve your FMCG Dashboard on the following domains:
- **Frontend**: https://retail.wersel.co.uk
- **Backend API**: https://retail-api.wersel.co.uk

## Prerequisites

- Server IP: `20.0.161.242`
- Docker containers running (frontend on port 3001, backend on port 8080)
- DNS records pointing to your server
- Root or sudo access on the server

---

## Step 1: DNS Configuration

Before proceeding, ensure your DNS records are properly configured:

```bash
# Check DNS propagation
nslookup retail.wersel.co.uk
nslookup retail-api.wersel.co.uk
```

Both should resolve to `20.0.161.242`. If not, add these A records in your DNS provider:

```
Type: A
Name: retail
Value: 20.0.161.242
TTL: 3600

Type: A
Name: retail-api
Value: 20.0.161.242
TTL: 3600
```

Wait for DNS propagation (can take up to 48 hours, but usually 5-30 minutes).

---

## Step 2: Install Certbot (Let's Encrypt SSL)

On your server (`20.0.161.242`), install Certbot:

```bash
# Update package list
sudo apt update

# Install Certbot and Nginx plugin
sudo apt install certbot python3-certbot-nginx -y

# Verify installation
certbot --version
```

---

## Step 3: Obtain SSL Certificates

### For Frontend Domain (retail.wersel.co.uk)

```bash
sudo certbot certonly --nginx \
  -d retail.wersel.co.uk \
  -d www.retail.wersel.co.uk \
  --non-interactive \
  --agree-tos \
  --email your-email@example.com
```

### For Backend Domain (retail-api.wersel.co.uk)

```bash
sudo certbot certonly --nginx \
  -d retail-api.wersel.co.uk \
  -d www.retail-api.wersel.co.uk \
  --non-interactive \
  --agree-tos \
  --email your-email@example.com
```

> **Note**: Replace `your-email@example.com` with your actual email address.

The certificates will be stored at:
- Frontend: `/etc/letsencrypt/live/retail.wersel.co.uk/`
- Backend: `/etc/letsencrypt/live/retail-api.wersel.co.uk/`

---

## Step 4: Deploy Nginx Configuration

### Copy the Nginx configuration to the server

On your **local machine**, upload the Nginx config to the server:

```bash
scp nginx/fmcg-retail.conf azureuser@20.0.161.242:/tmp/fmcg-retail.conf
```

### On the **server**, move it to Nginx sites-available:

```bash
# Move config to Nginx directory
sudo mv /tmp/fmcg-retail.conf /etc/nginx/sites-available/fmcg-retail.conf

# Create symbolic link to enable the site
sudo ln -sf /etc/nginx/sites-available/fmcg-retail.conf /etc/nginx/sites-enabled/fmcg-retail.conf

# Remove default Nginx config if it exists
sudo rm -f /etc/nginx/sites-enabled/default
```

---

## Step 5: Test and Reload Nginx

```bash
# Test Nginx configuration for syntax errors
sudo nginx -t

# If test passes, reload Nginx
sudo systemctl reload nginx

# Check Nginx status
sudo systemctl status nginx
```

Expected output:
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

---

## Step 6: Configure Firewall (if applicable)

Ensure ports 80 and 443 are open:

```bash
# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Check firewall status
sudo ufw status
```

---

## Step 7: Update Frontend Environment Variables

Update your frontend to use the new backend API URL.

### On your local machine:

Edit `frontend/.env.production`:

```env
REACT_APP_API_URL=https://retail-api.wersel.co.uk
```

### Rebuild and redeploy:

```bash
# On server
cd ~/fmcg-server/FMCG_Dashboard
docker-compose down
docker-compose up -d --build
```

---

## Step 8: Verify SSL Setup

### Test Frontend:

```bash
curl -I https://retail.wersel.co.uk
```

Expected: `HTTP/2 200` with SSL certificate info

### Test Backend API:

```bash
curl -I https://retail-api.wersel.co.uk/health
```

Expected: `HTTP/2 200` with JSON response

### Browser Test:

1. Open https://retail.wersel.co.uk in your browser
2. Check for the padlock icon (SSL is active)
3. Verify the dashboard loads correctly
4. Open DevTools → Network tab and verify API calls go to `https://retail-api.wersel.co.uk`

---

## Step 9: Auto-Renewal Setup

Certbot automatically sets up a cron job for certificate renewal. Verify it:

```bash
# Check renewal timer
sudo systemctl status certbot.timer

# Test renewal (dry run)
sudo certbot renew --dry-run
```

---

## Troubleshooting

### Issue: "Connection Refused" or "502 Bad Gateway"

**Solution**: Ensure Docker containers are running:

```bash
docker ps
```

You should see:
- `fmcg_frontend` (port 3001:80)
- `fmcg_backend` (port 8080:8080)
- `fmcg_mongodb` (port 27017:27017)

If not running:
```bash
cd ~/fmcg-server/FMCG_Dashboard
docker-compose up -d
```

---

### Issue: "SSL Certificate Not Found"

**Solution**: Re-run Certbot:

```bash
sudo certbot certonly --nginx -d retail.wersel.co.uk -d www.retail.wersel.co.uk
sudo certbot certonly --nginx -d retail-api.wersel.co.uk -d www.retail-api.wersel.co.uk
```

---

### Issue: "DNS Not Resolving"

**Solution**: Wait for DNS propagation or flush DNS cache:

```bash
# On server
sudo systemd-resolve --flush-caches

# On local machine (Windows)
ipconfig /flushdns
```

---

### Issue: CORS Errors in Browser Console

**Solution**: Update `docker-compose.yml` CORS settings:

```yaml
environment:
  - CORS_ORIGINS=https://retail.wersel.co.uk,http://localhost:3001
```

Then rebuild:
```bash
docker-compose down
docker-compose up -d --build
```

---

## Nginx Configuration Explained

The `fmcg-retail.conf` file contains:

1. **HTTP to HTTPS Redirect** (Port 80 → 443)
   - All HTTP traffic is automatically redirected to HTTPS

2. **SSL Configuration** (Port 443)
   - Uses Let's Encrypt certificates
   - TLS 1.2 and 1.3 support
   - Strong cipher suites

3. **Reverse Proxy**
   - Frontend: Proxies `https://retail.wersel.co.uk` → `http://localhost:3001`
   - Backend: Proxies `https://retail-api.wersel.co.uk` → `http://localhost:8080`

4. **Security Headers**
   - `X-Real-IP`: Preserves client IP
   - `X-Forwarded-For`: Proxy chain info
   - `X-Forwarded-Proto`: Original protocol (https)

---

## Quick Reference Commands

```bash
# Check Nginx status
sudo systemctl status nginx

# Reload Nginx (after config changes)
sudo nginx -t && sudo systemctl reload nginx

# View Nginx error logs
sudo tail -f /var/log/nginx/error.log

# View Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Check SSL certificate expiry
sudo certbot certificates

# Renew SSL certificates manually
sudo certbot renew

# Restart Docker containers
cd ~/fmcg-server/FMCG_Dashboard
docker-compose restart

# View container logs
docker logs fmcg_frontend
docker logs fmcg_backend
```

---

## Complete Deployment Flow (Summary)

```bash
# 1. Verify DNS
nslookup retail.wersel.co.uk

# 2. Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# 3. Obtain SSL certificates
sudo certbot certonly --nginx -d retail.wersel.co.uk -d www.retail.wersel.co.uk --email your-email@example.com --agree-tos
sudo certbot certonly --nginx -d retail-api.wersel.co.uk -d www.retail-api.wersel.co.uk --email your-email@example.com --agree-tos

# 4. Deploy Nginx config
sudo cp /path/to/fmcg-retail.conf /etc/nginx/sites-available/
sudo ln -sf /etc/nginx/sites-available/fmcg-retail.conf /etc/nginx/sites-enabled/

# 5. Test and reload Nginx
sudo nginx -t
sudo systemctl reload nginx

# 6. Rebuild Docker containers
cd ~/fmcg-server/FMCG_Dashboard
docker-compose down
docker-compose up -d --build

# 7. Verify
curl -I https://retail.wersel.co.uk
curl -I https://retail-api.wersel.co.uk/health
```

---

## Security Best Practices

1. **Enable HTTP/2**: Already configured in `fmcg-retail.conf`
2. **Strong SSL Ciphers**: TLS 1.2+ only
3. **Auto-renewal**: Certbot handles this automatically
4. **Firewall**: Only allow necessary ports (80, 443, 22)
5. **Regular Updates**: Keep Nginx and Certbot updated

```bash
sudo apt update && sudo apt upgrade -y
```

---

## Support

If you encounter issues:
1. Check Nginx logs: `sudo tail -f /var/log/nginx/error.log`
2. Check Docker logs: `docker logs fmcg_backend` or `docker logs fmcg_frontend`
3. Verify DNS: `nslookup retail.wersel.co.uk`
4. Test SSL: https://www.ssllabs.com/ssltest/

---

**Deployment Date**: 2026-01-14  
**Server IP**: 20.0.161.242  
**Domains**: retail.wersel.co.uk, retail-api.wersel.co.uk
