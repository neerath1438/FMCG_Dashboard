# FMCG Product Mastering Platform - Docker Deployment Guide

## Prerequisites

- Docker Desktop installed
- Docker Compose installed
- OpenAI API Key

## Quick Start (Single Command)

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-your-key-here

# 3. Start all services
docker-compose up -d

# 4. Access the application
# Frontend: http://YOUR_IP:3000
# Backend API: http://YOUR_IP:8000
# MongoDB: localhost:27017
```

## Detailed Commands

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mongodb
```

### Rebuild After Code Changes
```bash
docker-compose up -d --build
```

### Reset Everything (Including Database)
```bash
docker-compose down -v
docker-compose up -d
```

## Port Mapping

| Service  | Internal Port | External Port | Access URL |
|----------|---------------|---------------|------------|
| Frontend | 80            | 3000          | http://YOUR_IP:3000 |
| Backend  | 8000          | 8000          | http://YOUR_IP:8000 |
| MongoDB  | 27017         | 27017         | mongodb://YOUR_IP:27017 |

## For Client Deployment

### Option 1: Share Docker Compose (Recommended)
```bash
# Client runs:
docker-compose up -d

# Access via:
http://CLIENT_SERVER_IP:3000
```

### Option 2: Export as Docker Images
```bash
# Build and save images
docker save fmcg_backend:latest | gzip > fmcg_backend.tar.gz
docker save fmcg_frontend:latest | gzip > fmcg_frontend.tar.gz

# Client loads images
docker load < fmcg_backend.tar.gz
docker load < fmcg_frontend.tar.gz
docker-compose up -d
```

## Environment Variables

Create a `.env` file in the root directory:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

## Troubleshooting

### Port Already in Use
```bash
# Check what's using the port
netstat -ano | findstr :3000
netstat -ano | findstr :8000

# Stop conflicting services or change ports in docker-compose.yml
```

### Database Connection Issues
```bash
# Check MongoDB is running
docker-compose ps

# Check MongoDB logs
docker-compose logs mongodb
```

### Frontend Not Loading
```bash
# Rebuild frontend
docker-compose up -d --build frontend

# Check nginx logs
docker-compose logs frontend
```

## Production Recommendations

1. **Use Environment-Specific .env Files**
   - `.env.production`
   - `.env.staging`

2. **Enable HTTPS**
   - Add SSL certificates
   - Update nginx.conf

3. **Set Resource Limits**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 2G
   ```

4. **Use Docker Secrets for API Keys**
   - Don't commit `.env` to git
   - Use Docker secrets or external secret management

## Support

For issues, check:
1. Docker logs: `docker-compose logs`
2. Container status: `docker-compose ps`
3. Network connectivity: `docker network inspect fmcg_network`
