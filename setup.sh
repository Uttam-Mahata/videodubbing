#!/bin/bash
# Quick setup script for Video Dubbing Backend

set -e

echo "=========================================="
echo "Video Dubbing Backend Setup"
echo "=========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose found"
echo ""

# Start databases
echo "🚀 Starting MongoDB and Redis..."
docker-compose up -d mongodb redis

echo ""
echo "⏳ Waiting for databases to be ready..."
sleep 5

# Check database health
echo ""
echo "🔍 Checking database health..."

if docker exec videodubbing-mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
    echo "✅ MongoDB is healthy"
else
    echo "⚠️ MongoDB might not be ready yet. Please wait a moment and try again."
fi

if docker exec videodubbing-redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is healthy"
else
    echo "⚠️ Redis might not be ready yet. Please wait a moment and try again."
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "📊 Database Status:"
echo "  - MongoDB: mongodb://localhost:27017"
echo "  - Redis: redis://localhost:6379"
echo ""
echo "📝 Next Steps:"
echo "  1. Copy .env.example to .env and configure:"
echo "     cp backend/.env.example backend/.env"
echo ""
echo "  2. Install Python dependencies:"
echo "     pip install -r backend/requirements.txt"
echo ""
echo "  3. Test database connections:"
echo "     python backend/test_connections.py"
echo ""
echo "  4. Start the FastAPI application:"
echo "     python -m backend.main"
echo "     # or"
echo "     uvicorn backend.main:app --reload"
echo ""
echo "🎉 Happy coding!"
echo ""

# Optional: Start GUI tools
read -p "Would you like to start database GUI tools? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 Starting database GUI tools..."
    docker-compose --profile tools up -d
    echo ""
    echo "✅ GUI Tools started:"
    echo "  - Redis Commander: http://localhost:8081"
    echo "  - Mongo Express: http://localhost:8082 (admin/admin)"
    echo ""
fi
