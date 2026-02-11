# 🚀 Deployment Guide - Movie Recommender App

Your Django Movie Recommender app is now ready for deployment! Choose one of these hosting options based on your needs.

---

## 🌟 Recommended: Render (Free & Easy)

**Why Render?**
- ✅ Free tier available
- ✅ Automatic deployments from GitHub
- ✅ Easy setup (5 minutes)
- ✅ PostgreSQL database included
- ✅ Supports Python 3.11

### Step-by-Step Render Deployment

#### 1. Prepare Your Code

```powershell
# In your project directory
cd "C:\Users\adhit\Desktop\full stack development\project folder git\movie_recommender"

# Initialize git (if not already done)
git init
git add .
git commit -m "Prepare for deployment"

# Create a GitHub repository and push
git remote add origin https://github.com/yourusername/movie-recommender.git
git branch -M main
git push -u origin main
```

#### 2. Create Render Account

1. Go to https://render.com/
2. Sign up with GitHub (easiest)
3. Click **"New +"** → **"Web Service"**

#### 3. Configure Web Service

- **Connect Repository**: Select your `movie-recommender` repo
- **Name**: `movie-recommender` (or your choice)
- **Region**: Choose closest to you
- **Branch**: `main`
- **Root Directory**: Leave blank
- **Runtime**: `Python 3`
- **Build Command**:
  ```bash
  pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate
  ```
- **Start Command**:
  ```bash
  gunicorn movie_recommender.wsgi:application
  ```

#### 4. Set Environment Variables

Click **"Advanced"** → **"Add Environment Variable"**

Add these variables:

| Key | Value |
|-----|-------|
| `DEBUG` | `False` |
| `DJANGO_SECRET_KEY` | Generate at https://djecrety.ir/ |
| `ALLOWED_HOSTS` | `.onrender.com` |
| `TMDB_API_KEY` | `3658d16dd2e533776cb67b728a8f5a3c` |
| `GOOGLE_OAUTH_CLIENT_ID` | Your Google Client ID |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Your Google Secret |

#### 5. Deploy!

- Click **"Create Web Service"**
- Wait 5-10 minutes for deployment
- Your app will be live at `https://your-app-name.onrender.com`

#### 6. Update Google OAuth

1. Go to https://console.cloud.google.com/
2. Navigate to your OAuth credentials
3. Add redirect URI:
   ```
   https://your-app-name.onrender.com/accounts/google/login/callback/
   ```

#### 7. Create Superuser (Admin)

In Render dashboard:
- Go to your service → **"Shell"** tab
- Run:
  ```bash
  python manage.py createsuperuser
  ```

---

## 🐍 Option 2: PythonAnywhere (Beginner-Friendly)

**Why PythonAnywhere?**
- ✅ Free tier (3 months)
- ✅ Very beginner-friendly
- ✅ Web-based console
- ✅ No credit card required

### PythonAnywhere Deployment

#### 1. Create Account

1. Go to https://www.pythonanywhere.com/
2. Create a **free Beginner account**
3. Confirm your email

#### 2. Upload Your Code

**Option A: Git (Recommended)**
```bash
# In PythonAnywhere Bash console
git clone https://github.com/yourusername/movie-recommender.git
cd movie-recommender
```

**Option B: Manual Upload**
- Use the **Files** tab to upload your project folder

#### 3. Create Virtual Environment

```bash
# In Bash console
cd movie-recommender
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 4. Configure Web App

1. Go to **"Web"** tab
2. Click **"Add a new web app"**
3. Choose **"Manual configuration"** → **Python 3.11**
4. Set:
   - **Source code**: `/home/yourusername/movie-recommender`
   - **Working directory**: `/home/yourusername/movie-recommender`

#### 5. Edit WSGI File

Click on the WSGI configuration file link and replace with:

```python
import os
import sys

path = '/home/yourusername/movie-recommender'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'movie_recommender.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

#### 6. Set Environment Variables

In the **"Web"** tab, scroll to **"Environment variables"**:

| Key | Value |
|-----|-------|
| `DEBUG` | `False` |
| `DJANGO_SECRET_KEY` | Generate new key |
| `ALLOWED_HOSTS` | `.pythonanywhere.com` |
| `TMDB_API_KEY` | `3658d16dd2e533776cb67b728a8f5a3c` |

#### 7. Static Files

In **"Web"** tab → **"Static files"**:
- URL: `/static/`
- Directory: `/home/yourusername/movie-recommender/staticfiles`

Run in console:
```bash
python manage.py collectstatic
```

#### 8. Reload & Visit

- Click **"Reload"** button
- Visit `https://yourusername.pythonanywhere.com`

---

## 🚂 Option 3: Railway (Modern & Fast)

**Why Railway?**
- ✅ $5 free credit monthly
- ✅ Automatic deployments
- ✅ PostgreSQL included
- ✅ Very fast deployment

### Railway Deployment

#### 1. Install Railway CLI (Optional)

```powershell
# In PowerShell
npm install -g @railway/cli
# OR use the web dashboard
```

#### 2. Deploy via Dashboard

1. Go to https://railway.app/
2. Sign in with GitHub
3. Click **"New Project"** → **"Deploy from GitHub repo"**
4. Select your repository

#### 3. Add PostgreSQL (Optional)

- Click **"+ New"** → **"Database"** → **"PostgreSQL"**
- Railway will automatically set `DATABASE_URL`

#### 4. Set Environment Variables

Click your service → **"Variables"** tab:

```env
DEBUG=False
DJANGO_SECRET_KEY=your-generated-secret-key
ALLOWED_HOSTS=.railway.app
TMDB_API_KEY=3658d16dd2e533776cb67b728a8f5a3c
GOOGLE_OAUTH_CLIENT_ID=your-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
```

#### 5. Deploy!

- Railway automatically detects Django and deploys
- Your app will be at `https://your-app.railway.app`

---

## 📋 Pre-Deployment Checklist

Before deploying to any platform:

- [ ] Push code to GitHub
- [ ] Update `ALLOWED_HOSTS` in settings or environment variable
- [ ] Generate new `DJANGO_SECRET_KEY` for production
- [ ] Set `DEBUG=False` in production
- [ ] Add production domain to Google OAuth redirect URIs
- [ ] Test locally with `gunicorn movie_recommender.wsgi:application`
- [ ] Ensure all dependencies are in `requirements.txt`

---

## 🔧 Post-Deployment Tasks

After deploying:

### 1. Collect Static Files
```bash
python manage.py collectstatic --no-input
```

### 2. Run Migrations
```bash
python manage.py migrate
```

### 3. Create Superuser
```bash
python manage.py createsuperuser
```

### 4. Configure Google OAuth

Update redirect URIs in Google Cloud Console:
```
https://your-production-domain.com/accounts/google/login/callback/
```

### 5. Set up Social App in Admin

1. Go to `https://your-domain.com/admin/`
2. Navigate to **"Social applications"** → **"Add"**
3. Configure Google OAuth with production credentials

---

## 🐛 Common Issues & Solutions

### Issue: Static files not loading

**Solution**: Run `python manage.py collectstatic` and ensure `STATIC_ROOT` is set

### Issue: Database errors

**Solution**: Run `python manage.py migrate` on production

### Issue: Google OAuth redirect error

**Solution**: Add exact production URL to Google Console redirect URIs

### Issue: "DisallowedHost" error

**Solution**: Add your domain to `ALLOWED_HOSTS` environment variable

### Issue: 500 Internal Server Error

**Solution**: 
1. Set `DEBUG=True` temporarily to see error
2. Check logs in your hosting platform
3. Ensure all environment variables are set

---

## 📊 Monitoring & Maintenance

### Check Logs

**Render**: Dashboard → **"Logs"** tab
**PythonAnywhere**: Dashboard → **"Error log"**
**Railway**: Dashboard → **"Deployments"** → **"Logs"**

### Update Dependencies

```bash
pip install --upgrade django requests
pip freeze > requirements.txt
git commit -am "Update dependencies"
git push
```

### Backup Database

Export your database periodically:
```bash
python manage.py dumpdata > backup.json
```

---

## 💰 Cost Comparison

| Platform | Free Tier | Cost After | Best For |
|----------|-----------|------------|----------|
| **Render** | 750 hrs/month | $7/month | Best overall |
| **PythonAnywhere** | 3 months | $5/month | Beginners |
| **Railway** | $5 credit | $5-20/month | Developers |
| **Heroku** | No free tier | $7/month | Enterprise |

---

## 🎯 Recommended Choice

For your project, I recommend **Render** because:
- ✅ Easy setup with GitHub
- ✅ Free tier is generous
- ✅ Automatic HTTPS
- ✅ Good performance
- ✅ Easy to scale later

---

## 🆘 Need Help?

If you encounter issues:
1. Check the platform's documentation
2. Review error logs
3. Verify all environment variables are set
4. Ensure your domain is in `ALLOWED_HOSTS`
5. Check that Google OAuth redirect URIs match exactly

---

## 🚀 Ready to Deploy?

Choose your platform above and follow the step-by-step guide. Your movie recommender will be live in minutes!

**Quick Start with Render:**
```bash
# 1. Push to GitHub
git add .
git commit -m "Ready for deployment"
git push

# 2. Go to render.com and connect your repo
# 3. Add environment variables
# 4. Deploy!
```

Good luck! 🎬🍿
