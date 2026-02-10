# StrikeIQ Setup Script for Windows PowerShell
# This script sets up the development environment on Windows

Write-Host "🚀 Setting up StrikeIQ Options Market Intelligence Platform..." -ForegroundColor Green

# Check if Docker is installed
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not installed. Please install Docker Desktop for Windows first." -ForegroundColor Red
    exit 1
}

# Check if Docker Compose is installed
try {
    $composeVersion = docker-compose --version
    Write-Host "✅ Docker Compose found: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose is not installed. Please install Docker Compose first." -ForegroundColor Red
    exit 1
}

# Create necessary directories
Write-Host "📁 Creating directories..." -ForegroundColor Blue
New-Item -ItemType Directory -Force -Path "nginx/ssl" | Out-Null
New-Item -ItemType Directory -Force -Path "logs/backend" | Out-Null
New-Item -ItemType Directory -Force -Path "logs/frontend" | Out-Null
New-Item -ItemType Directory -Force -Path "data/postgres" | Out-Null

# Copy environment files if they don't exist
if (-not (Test-Path "backend/.env")) {
    Write-Host "📝 Creating backend environment file..." -ForegroundColor Blue
    Copy-Item "backend/.env.example" "backend/.env"
}

if (-not (Test-Path "frontend/.env.local")) {
    Write-Host "📝 Creating frontend environment file..." -ForegroundColor Blue
    Copy-Item "frontend/.env.example" "frontend/.env.local"
}

# Build and start services
Write-Host "🐳 Building Docker images..." -ForegroundColor Blue
docker-compose build

Write-Host "🚀 Starting services..." -ForegroundColor Blue
docker-compose up -d

# Wait for database to be ready
Write-Host "⏳ Waiting for database to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Run database migrations
Write-Host "🗄️ Running database migrations..." -ForegroundColor Blue
docker-compose exec backend alembic upgrade head

# Check if services are running
Write-Host "🔍 Checking service status..." -ForegroundColor Blue
docker-compose ps

Write-Host ""
Write-Host "✅ StrikeIQ setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Access the application at:" -ForegroundColor Cyan
Write-Host "   Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "   Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "   API Documentation: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "📊 Useful commands:" -ForegroundColor Cyan
Write-Host "   View logs: docker-compose logs -f" -ForegroundColor White
Write-Host "   Stop services: docker-compose down" -ForegroundColor White
Write-Host "   Restart services: docker-compose restart" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Development commands:" -ForegroundColor Cyan
Write-Host "   Backend shell: docker-compose exec backend bash" -ForegroundColor White
Write-Host "   Frontend shell: docker-compose exec frontend sh" -ForegroundColor White
Write-Host "   Database shell: docker-compose exec postgres psql -U strikeiq -d strikeiq" -ForegroundColor White
Write-Host ""
Write-Host "📚 For more information, see the README.md file." -ForegroundColor Cyan
