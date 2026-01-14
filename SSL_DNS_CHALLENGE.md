# SSL Setup - DNS Challenge Method (Quick Guide)

## பிரச்சனை (Problem)
Port 80 already vera production application use பண்றது, அதை stop பண்ண முடியாது.

## தீர்வு (Solution)
**DNS Challenge** method use பண்ணி SSL certificate generate பண்ணலாம். இது port 80 use பண்ணாது!

---

## Server-ல் Run பண்ண வேண்டியவை

### 1️⃣ Pull Latest Code
```bash
cd ~/fmcg-server/FMCG_Dashboard
git pull origin main
chmod +x setup-ssl-manual.sh
```

### 2️⃣ Run Manual SSL Setup
```bash
sudo ./setup-ssl-manual.sh
```

### 3️⃣ DNS TXT Records Add பண்ணுங்க

Script run பண்ணும்போது, இது மாதிரி message வரும்:

```
Please deploy a DNS TXT record under the name:
_acme-challenge.retail.wersel.co.uk

with the following value:
abc123xyz456def789ghi012jkl345mno678pqr901stu234vwx567yza890bcd123

Press Enter to Continue
```

**இப்போ என்ன பண்ணணும்:**

1. **Domain Provider-க்கு போங்க** (Cloudflare, GoDaddy, etc.)
2. **DNS Management section-க்கு போங்க**
3. **TXT Record add பண்ணுங்க:**
   ```
   Type: TXT
   Name: _acme-challenge.retail
   Value: abc123xyz456def789ghi012jkl345mno678pqr901stu234vwx567yza890bcd123
   TTL: 120 (or Auto)
   ```
4. **Save பண்ணுங்க**
5. **2-3 minutes wait பண்ணுங்க**
6. **Server terminal-ல் Enter press பண்ணுங்க**

### 4️⃣ Backend Domain-க்கும் Same Process

Script மறுபடியும் backend domain-க்கு TXT record கேக்கும். Same steps repeat பண்ணுங்க.

### 5️⃣ Docker Rebuild
```bash
docker-compose down
docker-compose up -d --build
```

### 6️⃣ Verify
```bash
curl -I https://retail.wersel.co.uk
```

---

## DNS TXT Record Example (Cloudflare)

```
Type: TXT
Name: _acme-challenge.retail
Content: <value from certbot>
TTL: Auto
Proxy: DNS only (grey cloud)
```

---

## Important Notes

- ✅ Production application-ஐ stop பண்ண தேவையில்லை
- ✅ Port 80 use பண்ணாது
- ⚠️ DNS TXT records add பண்ண access வேணும்
- ⚠️ ஒவ்வொரு domain-க்கும் separate TXT record வேணும்

---

## Troubleshooting

### TXT Record Verify பண்ணுவது எப்படி?

```bash
# Linux/Mac
dig _acme-challenge.retail.wersel.co.uk TXT

# Windows
nslookup -type=TXT _acme-challenge.retail.wersel.co.uk
```

### Certificate Generation Failed?

1. TXT record சரியா add பண்ணியிருக்கீங்களா check பண்ணுங்க
2. 2-3 minutes wait பண்ணுங்க (DNS propagation)
3. Script மறுபடியும் run பண்ணுங்க

---

## After SSL Setup

```bash
# Nginx reload
sudo systemctl reload nginx

# Docker rebuild
docker-compose down
docker-compose up -d --build

# Test
curl -I https://retail.wersel.co.uk
curl -I https://retail-api.wersel.co.uk
```

---

**Date**: 2026-01-14  
**Method**: DNS Challenge (Manual)  
**Email**: vishnu.t@wersel.io
