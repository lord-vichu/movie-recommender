# Quick Render Deployment Script
# This will help you prepare and push your code to GitHub for Render deployment

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RENDER DEPLOYMENT HELPER" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if git is installed
Write-Host "[1/6] Checking Git installation..." -ForegroundColor Yellow
$gitInstalled = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitInstalled) {
    Write-Host "  ❌ Git not found! Please install Git first:" -ForegroundColor Red
    Write-Host "     https://git-scm.com/download/win" -ForegroundColor White
    exit 1
}
Write-Host "  ✅ Git is installed" -ForegroundColor Green

# Check if in correct directory
Write-Host ""
Write-Host "[2/6] Checking project directory..." -ForegroundColor Yellow
if (-not (Test-Path "manage.py")) {
    Write-Host "  ❌ Error: manage.py not found!" -ForegroundColor Red
    Write-Host "     Please run this script from the movie_recommender directory" -ForegroundColor White
    exit 1
}
Write-Host "  ✅ In correct directory" -ForegroundColor Green

# Initialize git if needed
Write-Host ""
Write-Host "[3/6] Setting up Git repository..." -ForegroundColor Yellow
if (-not (Test-Path ".git")) {
    git init
    Write-Host "  ✅ Git repository initialized" -ForegroundColor Green
} else {
    Write-Host "  ✅ Git repository already exists" -ForegroundColor Green
}

# Create .gitignore if it doesn't exist
if (-not (Test-Path ".gitignore")) {
    @"
*.pyc
__pycache__/
db.sqlite3
.env
venv/
staticfiles/
*.log
"@ | Out-File -FilePath .gitignore -Encoding UTF8
    Write-Host "  ✅ Created .gitignore" -ForegroundColor Green
}

# Add files
Write-Host ""
Write-Host "[4/6] Adding files to Git..." -ForegroundColor Yellow
git add .
Write-Host "  ✅ Files staged" -ForegroundColor Green

# Commit
Write-Host ""
Write-Host "[5/6] Creating commit..." -ForegroundColor Yellow
$commitMessage = "Ready for Render deployment - $(Get-Date -Format 'yyyy-MM-dd')"
git commit -m $commitMessage
Write-Host "  ✅ Committed: $commitMessage" -ForegroundColor Green

# Instructions for GitHub
Write-Host ""
Write-Host "[6/6] Next Steps - Push to GitHub" -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  GITHUB SETUP REQUIRED" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1️⃣  Create a new repository on GitHub:" -ForegroundColor White
Write-Host "   👉 https://github.com/new" -ForegroundColor Cyan
Write-Host ""
Write-Host "2️⃣  Repository settings:" -ForegroundColor White
Write-Host "   • Name: movie-recommender (or your choice)" -ForegroundColor White
Write-Host "   • Visibility: Public or Private" -ForegroundColor White
Write-Host "   • Don't initialize with README" -ForegroundColor White
Write-Host ""
Write-Host "3️⃣  After creating, run these commands:" -ForegroundColor White
Write-Host ""
Write-Host "   git remote add origin https://github.com/YOUR_USERNAME/movie-recommender.git" -ForegroundColor Yellow
Write-Host "   git branch -M main" -ForegroundColor Yellow
Write-Host "   git push -u origin main" -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RENDER DEPLOYMENT" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "After pushing to GitHub:" -ForegroundColor White
Write-Host ""
Write-Host "1. Go to https://render.com/" -ForegroundColor Cyan
Write-Host "2. Sign up/Login with GitHub" -ForegroundColor White
Write-Host "3. Click 'New +' → 'Web Service'" -ForegroundColor White
Write-Host "4. Connect your repository" -ForegroundColor White
Write-Host "5. Add environment variables:" -ForegroundColor White
Write-Host ""
Write-Host "   DEBUG=False" -ForegroundColor Yellow
Write-Host "   DJANGO_SECRET_KEY=nd_6lx4=27@gwnbs0biba+sh3utaf##s_`$)qys#2^dblzf#s7@" -ForegroundColor Yellow
Write-Host "   ALLOWED_HOSTS=.onrender.com" -ForegroundColor Yellow
Write-Host "   TMDB_API_KEY=3658d16dd2e533776cb67b728a8f5a3c" -ForegroundColor Yellow
Write-Host ""
Write-Host "6. Click Create Web Service and wait!" -ForegroundColor White
Write-Host ""
Write-Host "Full guide: RENDER_DEPLOY.md" -ForegroundColor Cyan
Write-Host ""
Write-Host "Your code is ready! Now push to GitHub and deploy to Render!" -ForegroundColor Green
Write-Host ""
