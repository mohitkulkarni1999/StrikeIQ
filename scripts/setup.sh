#!/bin/bash

# StrikeIQ Setup Script
# This script sets up the development environment

set -e

echo "🚀 Setting up StrikeIQ Options Market Intelligence Platform..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p nginx/ssl
mkdir -p logs/backend
mkdir -p logs/frontend
mkdir -p data/postgres

# Set permissions
echo "🔒 Setting permissions..."
chmod +x scripts/*.sh

# Copy environment files if they don't exist
if [ ! -f backend/.env ]; then
    echo "📝 Creating backend environment file..."
    cp backend/.env.example backend/.env
fi

if [ ! -f frontend/.env.local ]; then
    echo "📝 Creating frontend environment file..."
    cp frontend/.env.example frontend/.env.local
fi

# Build and start services
echo "🐳 Building Docker images..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Run database migrations
echo "🗄️ Running database migrations..."
docker-compose exec backend alembic upgrade head

# Check if services are running
echo "🔍 Checking service status..."
docker-compose ps

echo ""
echo "✅ StrikeIQ setup complete!"
echo ""
echo "🌐 Access the application at:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Documentation: http://localhost:8000/docs"
echo ""
echo "📊 Useful commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "   Restart services: docker-compose restart"
echo ""
echo "🔧 Development commands:"
echo "   Backend shell: docker-compose exec backend bash"
echo "   Frontend shell: docker-compose exec frontend sh"
echo "   Database shell: docker-compose exec postgres psql -U strikeiq -d strikeiq"
echo ""
echo "📚 For more information, see the README.md file."
