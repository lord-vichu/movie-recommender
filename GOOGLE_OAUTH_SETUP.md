# Google OAuth Setup Guide

This guide will help you set up Google OAuth authentication for your CINE-M-AURA app.

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Select a project** → **NEW PROJECT**
3. Enter a project name (e.g., "CINE-M-AURA")
4. Click **CREATE**

## Step 2: Enable Google+ API (OAuth Consent)

1. In your project dashboard, go to **APIs & Services** → **OAuth consent screen**
2. Select **External** user type (unless you have a Google Workspace)
3. Click **CREATE**
4. Fill in the required fields:
   - **App name**: CINE-M-AURA
   - **User support email**: Your email
   - **Developer contact email**: Your email
5. Click **SAVE AND CONTINUE**
6. Skip the Scopes section (click **SAVE AND CONTINUE**)
7. Add test users (your email and any other testers)
8. Click **SAVE AND CONTINUE**

## Step 3: Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** → **OAuth client ID**
3. Select **Application type**: **Web application**
4. Enter a name (e.g., "CINE-M-AURA Web Client")
5. Add **Authorized redirect URIs**:
   ```
   http://127.0.0.1:8000/accounts/google/login/callback/
   http://localhost:8000/accounts/google/login/callback/
   ```
   
   **For production**, also add:
   ```
   https://yourdomain.com/accounts/google/login/callback/
   ```

6. Click **CREATE**
7. You'll see a popup with your **Client ID** and **Client Secret** - keep this open!

## Step 4: Configure Your Django App

### Option A: Using Environment Variables (Recommended)

1. Create a `.env` file in your project root:
   ```bash
   # In PowerShell
   cd "C:\Users\adhit\Desktop\full stack development\project folder git\movie_recommender"
   New-Item -Path .env -ItemType File
   ```

2. Add your credentials to `.env`:
   ```env
   GOOGLE_OAUTH_CLIENT_ID=your_client_id_here
   GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret_here
   ```

3. Install python-decouple:
   ```bash
   .\venv\Scripts\Activate.ps1
   pip install python-decouple
   ```

4. Update `settings.py` to use environment variables:
   ```python
   from decouple import config
   
   # In the SOCIALACCOUNT_PROVIDERS section:
   'APP': {
       'client_id': config('GOOGLE_OAUTH_CLIENT_ID'),
       'secret': config('GOOGLE_OAUTH_CLIENT_SECRET'),
       'key': ''
   }
   ```

### Option B: Using Django Admin (Easier for Testing)

1. Start your development server:
   ```bash
   .\venv\Scripts\Activate.ps1
   python manage.py runserver
   ```

2. Go to `http://127.0.0.1:8000/admin/`
3. Log in with your superuser account (create one if needed: `python manage.py createsuperuser`)
4. Go to **Social applications** → **Add social application**
5. Fill in:
   - **Provider**: Google
   - **Name**: Google OAuth
   - **Client id**: Paste your Client ID from Step 3
   - **Secret key**: Paste your Client Secret from Step 3
   - **Sites**: Select `example.com` and click the arrow to add it
6. Click **SAVE**

## Step 5: Test Google Login

1. Make sure your server is running
2. Go to `http://127.0.0.1:8000/`
3. Click **Sign in**
4. Click **Sign in with Google**
5. You should be redirected to Google's login page
6. After signing in, you'll be redirected directly back to your app homepage!

**Note:** The app is configured to skip intermediate pages and redirect users directly to the homepage after successful Google authentication. This provides a seamless login experience.

## Troubleshooting

### Error: "Redirect URI mismatch"
- Make sure the redirect URI in Google Cloud Console exactly matches what's in the error message
- Common variations:
  - `http://127.0.0.1:8000/accounts/google/login/callback/`
  - `http://localhost:8000/accounts/google/login/callback/`

### Error: "Social account not configured"
- Make sure you completed Step 4 (either Option A or B)
- Check that `SITE_ID = 1` is in your `settings.py`
- If using Django Admin method, verify the site ID matches

### Google button doesn't appear
- Make sure django-allauth is installed: `pip list | Select-String allauth`
- Check that all allauth apps are in `INSTALLED_APPS`
- Run migrations: `python manage.py migrate`

### Error: "Access blocked: This app's request is invalid"
- Complete the OAuth consent screen setup in Step 2
- Make sure you added your email as a test user

## Security Notes

- **Never commit** your `.env` file or credentials to Git
- Add `.env` to your `.gitignore` file
- In production, use proper environment variables or secrets management
- Consider using Django's built-in secret key rotation
- Enable HTTPS in production (required by Google OAuth)

## Next Steps

After successful setup:
1. Users can sign in with their Google account
2. Their profile info (name, email) will be automatically imported
3. They can use favorites, watch later, and library features
4. No need to remember another password!

## Additional Resources

- [Django Allauth Documentation](https://django-allauth.readthedocs.io/)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Cloud Console](https://console.cloud.google.com/)
