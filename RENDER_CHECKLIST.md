# ✅ Render Deployment Checklist

## 🎯 Quick Start (5 Minutes)

### Step 1: Prepare Your Code
```powershell
cd "C:\Users\adhit\Desktop\full stack development\project folder git\movie_recommender"
.\deploy_to_render.ps1
```

### Step 2: Create GitHub Repository
- Go to: https://github.com/new
- Name: `movie-recommender`
- Click **"Create repository"**

### Step 3: Push to GitHub
```powershell
git remote add origin https://github.com/YOUR_USERNAME/movie-recommender.git
git branch -M main
git push -u origin main
```

### Step 4: Deploy on Render
1. Go to: https://render.com/
2. Sign up with GitHub
3. Click **"New +"** → **"Web Service"**
4. Select your repository
5. Use these settings:

**Build Command:**
```bash
pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate
```

**Start Command:**
```bash
gunicorn movie_recommender.wsgi:application
```

**Environment Variables:**
```
DEBUG=False
DJANGO_SECRET_KEY=nd_6lx4=27@gwnbs0biba+sh3utaf##s_$)qys#2^dblzf#s7@
ALLOWED_HOSTS=.onrender.com
TMDB_API_KEY=3658d16dd2e533776cb67b728a8f5a3c
```

6. Click **"Create Web Service"**
7. Wait 5-10 minutes ⏱️
8. **Done!** Your app is live! 🎉

---

## 📋 Pre-Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] `requirements.txt` is up to date
- [ ] `Procfile` exists
- [ ] `runtime.txt` exists
- [ ] `.gitignore` excludes sensitive files
- [ ] Environment variables ready

---

## 🔑 Your Environment Variables

Copy these to Render:

```
DEBUG=False
DJANGO_SECRET_KEY=nd_6lx4=27@gwnbs0biba+sh3utaf##s_$)qys#2^dblzf#s7@
ALLOWED_HOSTS=.onrender.com
TMDB_API_KEY=3658d16dd2e533776cb67b728a8f5a3c
```

**Optional (Google OAuth):**
```
GOOGLE_OAUTH_CLIENT_ID=your-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
```

---

## ⏱️ Deployment Timeline

| Step | Time |
|------|------|
| Push to GitHub | 1 min |
| Create Render account | 1 min |
| Connect repository | 30 sec |
| Configure settings | 2 min |
| Build & deploy | 5-10 min |
| **Total** | **~10 min** |

---

## ✅ Post-Deployment

After deployment:

1. **Visit your URL**: `https://YOUR-APP-NAME.onrender.com`
2. **Test features**: Search, favorites, login
3. **Create admin**: Use Render Shell → `python manage.py createsuperuser`
4. **Setup Google OAuth** (optional): Add redirect URI to Google Console

---

## 🆘 Quick Troubleshooting

**Build failed?**
- Check logs in Render dashboard
- Verify `requirements.txt` is correct
- Ensure no syntax errors

**Static files not loading?**
- Verify build command includes `collectstatic`
- Check WhiteNoise is in middleware

**DisallowedHost error?**
- Add your Render URL to `ALLOWED_HOSTS`
- Format: `.onrender.com` or specific URL

---

## 📞 Help & Resources

- **Full Guide**: [RENDER_DEPLOY.md](RENDER_DEPLOY.md)
- **Render Docs**: https://render.com/docs/deploy-django
- **Community**: https://community.render.com/

---

## 🎉 Success!

Your Movie Recommender will be live at:
```
https://YOUR-APP-NAME.onrender.com
```

Share it with the world! 🌍🎬
