# StrikeIQ Development Script for Windows PowerShell
# This script starts the development environment with hot reload

Write-Host "🚀 Starting StrikeIQ Development Environment..." -ForegroundColor Green

# Check if services are running
$services = docker-compose ps
if ($services -notmatch "Up") {
    Write-Host "🐳 Starting services..." -ForegroundColor Blue
    docker-compose up -d
    Start-Sleep -Seconds 10
}

# Start backend in development mode
Write-Host "🔧 Starting backend in development mode..." -ForegroundColor Blue
docker-compose exec -d backend uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Start frontend in development mode
Write-Host "🎨 Starting frontend in development mode..." -ForegroundColor Blue
docker-compose exec -d frontend npm run dev

Write-Host ""
Write-Host "✅ Development environment started!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Access the application at:" -ForegroundColor Cyan
Write-Host "   Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "   Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "   API Documentation: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "📊 Development logs:" -ForegroundColor Cyan
Write-Host "   Backend: docker-compose logs -f backend" -ForegroundColor White
Write-Host "   Frontend: docker-compose logs -f frontend" -ForegroundColor White
Write-Host ""
Write-Host "🔄 Hot reload is enabled for both frontend and backend." -ForegroundColor Yellow
