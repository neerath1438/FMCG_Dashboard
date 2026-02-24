#!/bin/bash

# Server Debugging Script for FMCG Dashboard
echo "========================================="
echo "FMCG Dashboard - Server Diagnostics"
echo "========================================="

# 1. Check Git status
echo ""
echo "1. Git Status:"
git log -1 --oneline
echo ""

# 2. Check Docker containers
echo "2. Docker Container Status:"
docker compose ps
echo ""

# 3. Check backend logs (last 50 lines)
echo "3. Backend Logs (last 50 lines):"
docker compose logs --tail=50 backend
echo ""

# 4. Check MongoDB connection
echo "4. MongoDB Connection Test:"
docker compose exec backend python -c "
from backend.database import get_collection
try:
    coll = get_collection('MASTER_STOCK')
    count = coll.count_documents({})
    print(f'✓ MongoDB connected. MASTER_STOCK count: {count}')
except Exception as e:
    print(f'✗ MongoDB error: {e}')
"
echo ""

# 5. Check environment variables
echo "5. Environment Variables (Backend):"
docker compose exec backend env | grep -E "(MONGO_URI|AZURE|OPENAI)" | sed 's/=.*/=***HIDDEN***/'
echo ""

# 6. Test backend API
echo "6. Backend API Test:"
curl -s http://localhost:8000/dashboard/summary | python -m json.tool
echo ""

# 7. Check if data directory exists
echo "7. Data Directory Check:"
docker compose exec backend ls -la /app/data/ 2>/dev/null || echo "Data directory not found"
echo ""

echo "========================================="
echo "Diagnostics Complete"
echo "========================================="
