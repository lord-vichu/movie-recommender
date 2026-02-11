# 🚀 Deploy to Render - Step by Step

## Prerequisites
- GitHub account
- Render account (sign up at https://render.com)

---

## 📋 Deployment Steps

### 1. Push Your Code to GitHub

```powershell
# Navigate to your project
cd "C:\Users\adhit\Desktop\full stack development\project folder git\movie_recommender"

# Initialize git (if not done)
git init

# Add all files
git add .

# Commit
git commit -m "Ready for Render deployment"

# Create a GitHub repository at https://github.com/new
# Then connect and push:
git remote add origin https://github.com/YOUR_USERNAME/movie-recommender.git
git branch -M main
git push -u origin main
```

### 2. Create Render Account

1. Go to https://render.com/
2. Click **"Get Started for Free"**
3. Sign up with GitHub (recommended)
4. Authorize Render to access your GitHub

### 3. Create New Web Service

1. Click **"New +"** (top right)
2. Select **"Web Service"**
3. Connect your `movie-recommender` repository
4. If you don't see it, click **"Configure account"** and grant access

### 4. Configure Your Service

**Basic Settings:**
- **Name**: `movie-recommender` (or your choice)
- **Region**: Choose closest to you
- **Branch**: `main`
- **Root Directory**: (leave blank)
- **Runtime**: `Python 3`

**Build & Deploy:**
- **Build Command**:
  ```bash
  pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate
  ```
  
- **Start Command**:
  ```bash
  gunicorn movie_recommender.wsgi:application
  ```

**Plan:**
- Select **"Free"** plan

### 5. Set Environment Variables

Click **"Advanced"** → **"Add Environment Variable"**

Add these **one by one**:

| Key | Value |
|-----|-------|
| `DEBUG` | `False` |
| `DJANGO_SECRET_KEY` | `nd_6lx4=27@gwnbs0biba+sh3utaf##s_$)qys#2^dblzf#s7@` |
| `ALLOWED_HOSTS` | `.onrender.com` |
| `TMDB_API_KEY` | `3658d16dd2e533776cb67b728a8f5a3c` |

**Optional (for Google OAuth):**

| Key | Value |
|-----|-------|
| `GOOGLE_OAUTH_CLIENT_ID` | Your Client ID from Google Console |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Your Client Secret from Google Console |

### 6. Deploy!

1. Click **"Create Web Service"**
2. Wait 5-10 minutes while Render:
   - Installs dependencies
   - Collects static files
   - Runs migrations
   - Starts your app

3. Watch the logs in real-time
4. You'll see "Build successful" and "Your service is live"

### 7. Get Your URL

Your app will be available at:
```
https://movie-recommender.onrender.com
```
(or your custom name)

---

## ✅ Post-Deployment Tasks

### 1. Test Your App

Visit your URL and verify:
- ✅ Homepage loads
- ✅ Movies display
- ✅ Search works
- ✅ Theme toggle works

### 2. Create Admin User

In Render dashboard:
1. Go to your service
2. Click **"Shell"** tab (top right)
3. Run:
   ```bash
   python manage.py createsuperuser
   ```
4. Enter username, email, password

### 3. Configure Google OAuth (if using)

1. Go to https://console.cloud.google.com/
2. Navigate to your OAuth credentials
3. Add authorized redirect URI:
   ```
   https://YOUR-APP-NAME.onrender.com/accounts/google/login/callback/
   ```

4. In your app admin panel (`https://YOUR-APP-NAME.onrender.com/admin/`):
   - Go to **Social applications** → **Add social application**
   - Provider: **Google**
   - Client ID: Paste your Google Client ID
   - Secret key: Paste your Google Client Secret
   - Sites: Select and add **example.com**
   - Save

---

## 🔧 Managing Your Deployment

### View Logs

In Render dashboard:
- Go to your service
- Click **"Logs"** tab
- See real-time application logs

### Update Your App

```bash
# Make changes locally
# Then commit and push
git add .
git commit -m "Update features"
git push

# Render will automatically redeploy!
```

### Manual Deploy

In Render dashboard:
- Click **"Manual Deploy"** → **"Deploy latest commit"**

### Environment Variables

To update:
1. Go to **"Environment"** tab
2. Click **"Add Environment Variable"** or edit existing
3. Save (triggers automatic redeploy)

---

## 🐛 Troubleshooting

### Build Failed

**Check these:**
1. `requirements.txt` has all dependencies
2. No syntax errors in your code
3. Check build logs for specific error

**Common fixes:**
```bash
# Update requirements locally
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update requirements"
git push
```

### Static Files Not Loading

**Solution 1:** Verify `collectstatic` in build command
```bash
pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate
```

**Solution 2:** Check settings.py has:
```python
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### DisallowedHost Error

**Solution:** Update environment variable:
```
ALLOWED_HOSTS=.onrender.com,movie-recommender.onrender.com
```

### Application Not Responding

1. Check **Logs** tab for errors
2. Verify start command is correct
3. Check that migrations ran successfully
4. Try manual deploy

### Google OAuth Error

**Solution:** Update redirect URI in Google Console:
```
https://YOUR-APP-NAME.onrender.com/accounts/google/login/callback/
```

Make sure it matches EXACTLY (including trailing slash).

---

## 📊 Monitor Your App

### Health Checks

Render automatically monitors your app:
- **Status**: Green = healthy, Red = down
- **Last Deploy**: See deployment history
- **Metrics**: View response times, memory usage

### Set Up Alerts

1. Go to **"Settings"** tab
2. Add email for notifications
3. Render will alert you if your app goes down

---

## 💰 Free Tier Limits

Render Free Tier includes:
- ✅ 750 hours/month (enough for 24/7 uptime)
- ✅ 512 MB RAM
- ✅ Automatic HTTPS
- ✅ Custom domains
- ⚠️ Spins down after 15 minutes of inactivity
- ⚠️ Cold starts (takes 30s to wake up)

### Upgrade to Paid ($7/month)
- No spin down
- Faster performance
- More RAM
- Priority support

---

## 🎯 Success Checklist

After deployment, verify:
- [ ] App loads at your Render URL
- [ ] Movies display correctly
- [ ] Search and filters work
- [ ] User registration works
- [ ] Login/logout works
- [ ] Favorites, watch later, library features work
- [ ] Google OAuth configured (if using)
- [ ] Admin panel accessible
- [ ] Static files (CSS/JS) loading
- [ ] Dark/light theme toggle works

---

## 🔐 Security Reminders

- ✅ `DEBUG=False` in production
- ✅ Strong `DJANGO_SECRET_KEY`
- ✅ `ALLOWED_HOSTS` properly configured
- ✅ Don't commit `.env` files to Git
- ✅ Use environment variables for secrets

---

## 🚀 You're Live!

Once deployed, share your movie recommender:
```
https://YOUR-APP-NAME.onrender.com
```

**What users can do:**
- 🔍 Search and discover movies
- ⭐ Add favorites
- ⏰ Create watch later list
- 📚 Build personal library
- 🔐 Sign in with Google
- 🌓 Toggle dark/light theme
- 📖 Read Wikipedia summaries

---

## 📞 Need Help?

- **Render Docs**: https://render.com/docs
- **Render Community**: https://community.render.com/
- **Check Logs**: Most issues show up in logs
- **Django Docs**: https://docs.djangoproject.com/

---

## 🎉 Congratulations!

Your Movie Recommender is now live on the internet!

**Next steps:**
1. Test all features
2. Share with friends
3. Get feedback
4. Add custom domain (optional)
5. Consider upgrading for better performance

Enjoy your deployed app! 🎬🍿
