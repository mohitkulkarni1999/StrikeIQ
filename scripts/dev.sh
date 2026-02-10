#!/bin/bash

# StrikeIQ Development Script
# This script starts the development environment with hot reload

set -e

echo "🚀 Starting StrikeIQ Development Environment..."

# Check if services are running
if ! docker-compose ps | grep -q "Up"; then
    echo "🐳 Starting services..."
    docker-compose up -d
    sleep 10
fi

# Start backend in development mode
echo "🔧 Starting backend in development mode..."
docker-compose exec -d backend uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Start frontend in development mode
echo "🎨 Starting frontend in development mode..."
docker-compose exec -d frontend npm run dev

echo ""
echo "✅ Development environment started!"
echo ""
echo "🌐 Access the application at:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Documentation: http://localhost:8000/docs"
echo ""
echo "📊 Development logs:"
echo "   Backend: docker-compose logs -f backend"
echo "   Frontend: docker-compose logs -f frontend"
echo ""
echo "🔄 Hot reload is enabled for both frontend and backend."
