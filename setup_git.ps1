# Quick Git Setup Script
# Run this to prepare your code for GitHub and deployment

Write-Host "=" -NoNewline; Write-Host ("=" * 69)
Write-Host " 🚀 GIT SETUP & DEPLOYMENT HELPER"
Write-Host "=" -NoNewline; Write-Host ("=" * 69)

# Check if git is installed
try {
    git --version | Out-Null
    Write-Host "`n✅ Git is installed"
} catch {
    Write-Host "`n❌ Git is not installed!"
    Write-Host "   Download from: https://git-scm.com/download/win"
    exit 1
}

# Check if already a git repository
if (Test-Path ".git") {
    Write-Host "✅ Git repository already initialized"
} else {
    Write-Host "`n📦 Initializing Git repository..."
    git init
    Write-Host "✅ Git initialized"
}

# Check if .gitignore exists
if (Test-Path ".gitignore") {
    Write-Host "✅ .gitignore exists"
} else {
    Write-Host "⚠️  .gitignore not found (but should exist)"
}

# Show current status
Write-Host "`n" + ("=" * 70)
Write-Host " 📊 GIT STATUS"
Write-Host ("=" * 70)
git status --short

# Ask to stage files
Write-Host "`n" + ("=" * 70)
Write-Host " 📝 STAGING FILES"
Write-Host ("=" * 70)
$stage = Read-Host "`nStage all files for commit? (y/n)"

if ($stage -eq 'y') {
    git add .
    Write-Host "✅ All files staged"
    Write-Host "`nStaged files:"
    git status --short
} else {
    Write-Host "⏭️  Skipping staging"
}

# Commit
Write-Host "`n" + ("=" * 70)
Write-Host " 💾 COMMIT"
Write-Host ("=" * 70)
$commit = Read-Host "`nCreate commit? (y/n)"

if ($commit -eq 'y') {
    $message = Read-Host "Enter commit message (or press Enter for default)"
    if ([string]::IsNullOrWhiteSpace($message)) {
        $message = "Initial commit - Movie Recommender ready for deployment"
    }
    
    git commit -m "$message"
    Write-Host "✅ Commit created"
} else {
    Write-Host "⏭️  Skipping commit"
}

# Check for remote
Write-Host "`n" + ("=" * 70)
Write-Host " 🔗 GITHUB REMOTE"
Write-Host ("=" * 70)

$remotes = git remote -v 2>$null
if ($remotes) {
    Write-Host "✅ Remote repository configured:"
    Write-Host $remotes
    
    $push = Read-Host "`nPush to remote? (y/n)"
    if ($push -eq 'y') {
        $branch = git branch --show-current
        Write-Host "`nPushing to remote..."
        git push -u origin $branch
        Write-Host "✅ Code pushed to GitHub!"
    }
} else {
    Write-Host "⚠️  No remote repository configured"
    Write-Host "`nTo add a remote:"
    Write-Host "1. Create a new repository on GitHub"
    Write-Host "2. Run this command:"
    Write-Host "   git remote add origin https://github.com/yourusername/movie-recommender.git"
    Write-Host "3. Then push:"
    Write-Host "   git branch -M main"
    Write-Host "   git push -u origin main"
}

# Deployment instructions
Write-Host "`n" + ("=" * 70)
Write-Host " 🚀 NEXT STEPS: DEPLOYMENT"
Write-Host ("=" * 70)

Write-Host "`n✅ Your code is ready for deployment!"
Write-Host "`nRecommended hosting platforms:"
Write-Host ""
Write-Host "1. 🌟 RENDER (Easiest, Free)"
Write-Host "   - Go to: https://render.com/"
Write-Host "   - Sign up with GitHub"
Write-Host "   - Click 'New Web Service'"
Write-Host "   - Select your repository"
Write-Host "   - Add environment variables (see DEPLOYMENT_SUMMARY.md)"
Write-Host "   - Deploy!"
Write-Host ""
Write-Host "2. 🐍 PYTHONANYWHERE (Beginner-friendly)"
Write-Host "   - Go to: https://pythonanywhere.com/"
Write-Host "   - Free tier for 3 months"
Write-Host "   - Web-based file upload"
Write-Host ""
Write-Host "3. 🚂 RAILWAY (Modern, Fast)"
Write-Host "   - Go to: https://railway.app/"
Write-Host "   - $5/month credit"
Write-Host "   - Automatic deployments"

Write-Host "`n📚 Full deployment guide: DEPLOYMENT.md"
Write-Host "📋 Quick summary: DEPLOYMENT_SUMMARY.md"
Write-Host "🔧 Pre-deployment check: python check_deployment.py"

Write-Host "`n" + ("=" * 70)
Write-Host " 🎯 ENVIRONMENT VARIABLES FOR PRODUCTION"
Write-Host ("=" * 70)

Write-Host "`nAdd these to your hosting platform:"
Write-Host ""
Write-Host "DEBUG=False"
Write-Host "DJANGO_SECRET_KEY=nd_6lx4=27@gwnbs0biba+sh3utaf##s_`$)qys#2^dblzf#s7@"
Write-Host "ALLOWED_HOSTS=.onrender.com"
Write-Host "TMDB_API_KEY=3658d16dd2e533776cb67b728a8f5a3c"
Write-Host "GOOGLE_OAUTH_CLIENT_ID=your-client-id"
Write-Host "GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret"

Write-Host "`n" + ("=" * 70)
Write-Host " ✨ Good luck with your deployment!"
Write-Host ("=" * 70)
