# SSL Deployment Checklist

## Pre-Deployment
- [ ] DNS A records created for `retail.wersel.co.uk` → `20.0.161.242`
- [ ] DNS A records created for `retail-api.wersel.co.uk` → `20.0.161.242`
- [ ] DNS propagation verified (use `nslookup` or https://dnschecker.org)
- [ ] SSH access to server confirmed
- [ ] Docker containers running on server

---

## File Upload
- [ ] Upload `nginx/fmcg-retail.conf` to server `/tmp/`
- [ ] Upload `setup-ssl.sh` to server `/tmp/`
- [ ] Make `setup-ssl.sh` executable (`chmod +x`)
- [ ] Update email address in `setup-ssl.sh`

---

## SSL Certificate Generation
- [ ] Certbot installed on server
- [ ] SSL certificate obtained for `retail.wersel.co.uk`
- [ ] SSL certificate obtained for `retail-api.wersel.co.uk`
- [ ] Certificates verified at `/etc/letsencrypt/live/`

---

## Nginx Configuration
- [ ] Nginx config copied to `/etc/nginx/sites-available/`
- [ ] Symbolic link created in `/etc/nginx/sites-enabled/`
- [ ] Default Nginx site removed
- [ ] Nginx configuration tested (`sudo nginx -t`)
- [ ] Nginx reloaded/restarted

---

## Firewall & Security
- [ ] Port 80 (HTTP) opened
- [ ] Port 443 (HTTPS) opened
- [ ] UFW/firewall rules verified

---

## Docker Configuration
- [ ] `docker-compose.yml` CORS settings updated
- [ ] `frontend/.env.production` API URL verified
- [ ] Docker containers stopped
- [ ] Docker containers rebuilt (`docker-compose up -d --build`)
- [ ] All 3 containers running (frontend, backend, mongodb)

---

## Verification
- [ ] Frontend accessible via HTTPS: https://retail.wersel.co.uk
- [ ] Backend API accessible via HTTPS: https://retail-api.wersel.co.uk
- [ ] SSL padlock icon visible in browser
- [ ] No SSL certificate warnings
- [ ] Dashboard loads correctly
- [ ] API calls working (check browser DevTools → Network)
- [ ] No CORS errors in console

---

## Testing
- [ ] `curl -I https://retail.wersel.co.uk` returns 200
- [ ] `curl -I https://retail-api.wersel.co.uk/health` returns 200
- [ ] SSL Labs test passed: https://www.ssllabs.com/ssltest/
- [ ] Mobile browser test completed
- [ ] Different browser test (Chrome, Firefox, Safari)

---

## Auto-Renewal Setup
- [ ] Certbot timer active (`sudo systemctl status certbot.timer`)
- [ ] Dry-run renewal test passed (`sudo certbot renew --dry-run`)
- [ ] Renewal cron job verified

---

## Documentation
- [ ] SSL_DEPLOYMENT_GUIDE.md reviewed
- [ ] SSL_SETUP_TAMIL.md reviewed
- [ ] Team members notified of new URLs
- [ ] DNS records documented
- [ ] Server credentials secured

---

## Post-Deployment
- [ ] Monitor Nginx logs for errors
- [ ] Monitor Docker container logs
- [ ] Set up uptime monitoring (optional)
- [ ] Update any hardcoded URLs in code
- [ ] Update API documentation with new URLs
- [ ] Test all major features of the application

---

## Troubleshooting (If Issues Occur)

### Issue: 502 Bad Gateway
- [ ] Check Docker containers: `docker ps`
- [ ] Restart containers: `docker-compose restart`
- [ ] Check Nginx logs: `sudo tail -f /var/log/nginx/error.log`

### Issue: SSL Certificate Error
- [ ] Verify certificates exist: `sudo certbot certificates`
- [ ] Re-run Certbot if needed
- [ ] Check certificate paths in Nginx config

### Issue: CORS Errors
- [ ] Verify CORS_ORIGINS in `docker-compose.yml`
- [ ] Rebuild containers: `docker-compose down && docker-compose up -d --build`
- [ ] Check browser console for specific errors

### Issue: DNS Not Resolving
- [ ] Wait for DNS propagation (5-30 minutes)
- [ ] Clear DNS cache on server and local machine
- [ ] Verify DNS records in domain registrar

---

## Quick Commands Reference

```bash
# Check everything is running
docker ps
sudo systemctl status nginx
sudo certbot certificates

# View logs
sudo tail -f /var/log/nginx/error.log
docker logs -f fmcg_backend

# Restart services
sudo systemctl restart nginx
docker-compose restart

# Test endpoints
curl -I https://retail.wersel.co.uk
curl -I https://retail-api.wersel.co.uk/health
```

---

## Completion Sign-off

**Deployment Date**: _______________  
**Deployed By**: _______________  
**Server IP**: 20.0.161.242  
**Frontend URL**: https://retail.wersel.co.uk  
**Backend URL**: https://retail-api.wersel.co.uk  

**Status**: 
- [ ] ✅ Deployment Successful
- [ ] ⚠️ Deployment Completed with Issues (document below)
- [ ] ❌ Deployment Failed (document below)

**Notes**:
```
[Add any notes, issues encountered, or special configurations here]
```

---

**Next SSL Renewal Date**: _______________  
(Certificates expire in 90 days, auto-renewal happens at 60 days)
