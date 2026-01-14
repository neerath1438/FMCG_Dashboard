# SSL Setup Quick Reference (Tamil)

## உங்கள் புதிய டொமைன்கள்
- **Frontend**: https://retail.wersel.co.uk
- **Backend API**: https://retail-api.wersel.co.uk
- **Server IP**: 20.0.161.242

---

## முழு செயல்முறை (Complete Flow)

### 1️⃣ DNS சரிபார்ப்பு (DNS Verification)
```bash
nslookup retail.wersel.co.uk
nslookup retail-api.wersel.co.uk
```
இரண்டும் `20.0.161.242` ஐ காட்ட வேண்டும்.

---

### 2️⃣ Server-ல் Files Upload செய்யவும்

**உங்கள் Local Machine-ல்:**
```bash
# Nginx config upload
scp nginx/fmcg-retail.conf azureuser@20.0.161.242:/tmp/

# SSL setup script upload
scp setup-ssl.sh azureuser@20.0.161.242:/tmp/
```

---

### 3️⃣ Server-ல் SSL Setup

**Server-ல் SSH செய்யவும்:**
```bash
ssh azureuser@20.0.161.242
```

**Script-ஐ run செய்யவும்:**
```bash
cd /tmp
chmod +x setup-ssl.sh

# முக்கியம்: Email address மாற்றவும்!
sudo nano setup-ssl.sh
# EMAIL="your-email@example.com" என்பதை உங்கள் email-ஆக மாற்றவும்

# Script run செய்யவும்
sudo ./setup-ssl.sh
```

---

### 4️⃣ Docker Containers Restart

```bash
cd ~/fmcg-server/FMCG_Dashboard

# Stop containers
docker-compose down

# Rebuild and start
docker-compose up -d --build

# Check status
docker ps
```

நீங்கள் பார்க்க வேண்டியவை:
- ✅ `fmcg_frontend` (port 3001:80)
- ✅ `fmcg_backend` (port 8080:8080)
- ✅ `fmcg_mongodb` (port 27017:27017)

---

### 5️⃣ சரிபார்ப்பு (Verification)

**Browser-ல் திறக்கவும்:**
- https://retail.wersel.co.uk

**பார்க்க வேண்டியவை:**
- 🔒 Padlock icon (SSL active)
- Dashboard load ஆகுதா
- Console-ல் errors இல்லையா

**Terminal-ல் test:**
```bash
# Frontend test
curl -I https://retail.wersel.co.uk

# Backend test
curl -I https://retail-api.wersel.co.uk/health
```

---

## பொதுவான பிரச்சனைகள் (Common Issues)

### ❌ "502 Bad Gateway"
**காரணம்**: Docker containers run ஆகல

**தீர்வு**:
```bash
cd ~/fmcg-server/FMCG_Dashboard
docker-compose up -d
docker ps  # Check containers
```

---

### ❌ "SSL Certificate Error"
**காரணம்**: Certificate சரியாக generate ஆகல

**தீர்வு**:
```bash
# Re-run Certbot
sudo certbot certonly --nginx \
  -d retail.wersel.co.uk \
  -d www.retail.wersel.co.uk \
  --email your-email@example.com \
  --agree-tos

sudo certbot certonly --nginx \
  -d retail-api.wersel.co.uk \
  -d www.retail-api.wersel.co.uk \
  --email your-email@example.com \
  --agree-tos

# Restart Nginx
sudo systemctl restart nginx
```

---

### ❌ CORS Error (Browser Console-ல்)
**காரணம்**: Backend CORS settings தவறு

**தீர்வு**:
```bash
cd ~/fmcg-server/FMCG_Dashboard

# Edit docker-compose.yml
nano docker-compose.yml

# CORS_ORIGINS-ல் இது இருக்கா பாருங்க:
# CORS_ORIGINS=http://localhost:3001,http://127.0.0.1:3001,https://retail.wersel.co.uk

# Rebuild
docker-compose down
docker-compose up -d --build
```

---

### ❌ DNS Not Resolving
**காரணம்**: DNS propagation ஆகல

**தீர்வு**:
```bash
# Wait 5-30 minutes
# Check DNS propagation: https://dnschecker.org

# Server-ல் DNS cache clear
sudo systemd-resolve --flush-caches

# Local machine-ல் (Windows):
ipconfig /flushdns
```

---

## முக்கிய Commands (Important Commands)

### Nginx Commands
```bash
# Status check
sudo systemctl status nginx

# Restart
sudo systemctl restart nginx

# Reload (config changes-க்கு)
sudo nginx -t && sudo systemctl reload nginx

# Error logs
sudo tail -f /var/log/nginx/error.log

# Access logs
sudo tail -f /var/log/nginx/access.log
```

### Docker Commands
```bash
# Container status
docker ps

# Restart all
docker-compose restart

# Rebuild all
docker-compose down
docker-compose up -d --build

# View logs
docker logs fmcg_frontend
docker logs fmcg_backend

# Follow logs (real-time)
docker logs -f fmcg_backend
```

### SSL Certificate Commands
```bash
# Certificate info
sudo certbot certificates

# Renew manually
sudo certbot renew

# Test renewal (dry run)
sudo certbot renew --dry-run

# Certificate expiry check
sudo openssl x509 -in /etc/letsencrypt/live/retail.wersel.co.uk/cert.pem -noout -dates
```

---

## Files Modified (மாற்றப்பட்ட Files)

1. ✅ `nginx/fmcg-retail.conf` - Nginx configuration (already exists)
2. ✅ `docker-compose.yml` - CORS settings updated
3. ✅ `frontend/.env.production` - Backend URL updated (already correct)
4. ✅ `setup-ssl.sh` - Automated setup script (new)
5. ✅ `SSL_DEPLOYMENT_GUIDE.md` - Full documentation (new)

---

## Auto-Renewal (தானாக Renewal)

Certbot automatically renews certificates **60 days-க்கு முன்**.

**Check auto-renewal:**
```bash
sudo systemctl status certbot.timer
```

**Manual renewal test:**
```bash
sudo certbot renew --dry-run
```

---

## Security Checklist

- ✅ HTTPS enabled (TLS 1.2 + 1.3)
- ✅ HTTP → HTTPS redirect
- ✅ Strong SSL ciphers
- ✅ Auto-renewal enabled
- ✅ Firewall configured (ports 80, 443)
- ✅ CORS properly configured
- ✅ Docker containers isolated

---

## Support & Monitoring

### SSL Test
https://www.ssllabs.com/ssltest/analyze.html?d=retail.wersel.co.uk

### DNS Propagation Check
https://dnschecker.org

### Uptime Monitoring
Consider setting up:
- UptimeRobot (free)
- Pingdom
- StatusCake

---

## Contact Info

**Server**: 20.0.161.242  
**Frontend**: https://retail.wersel.co.uk  
**Backend**: https://retail-api.wersel.co.uk  
**Setup Date**: 2026-01-14

---

## Quick Start (மிக விரைவான முறை)

```bash
# 1. Upload files
scp nginx/fmcg-retail.conf azureuser@20.0.161.242:/tmp/
scp setup-ssl.sh azureuser@20.0.161.242:/tmp/

# 2. SSH to server
ssh azureuser@20.0.161.242

# 3. Run setup
cd /tmp
chmod +x setup-ssl.sh
sudo nano setup-ssl.sh  # Change email
sudo ./setup-ssl.sh

# 4. Restart Docker
cd ~/fmcg-server/FMCG_Dashboard
docker-compose down
docker-compose up -d --build

# 5. Test
curl -I https://retail.wersel.co.uk
```

**முடிந்தது! (Done!)** 🎉

Browser-ல் https://retail.wersel.co.uk திறந்து பாருங்கள்.
