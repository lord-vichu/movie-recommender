# Quick Google OAuth Setup Script
# Run this to easily configure Google OAuth via Django Admin

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movie_recommender.settings')
django.setup()

from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

print("=" * 60)
print("GOOGLE OAUTH CONFIGURATION HELPER")
print("=" * 60)

# Check for superuser
superusers = User.objects.filter(is_superuser=True)
if not superusers.exists():
    print("\n⚠️  No superuser account found!")
    print("Creating a superuser account...\n")
    username = input("Enter admin username (default: admin): ").strip() or "admin"
    email = input("Enter admin email: ").strip()
    password = input("Enter admin password: ").strip()
    
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"✅ Superuser '{username}' created successfully!")
else:
    print(f"✅ Found superuser account: {superusers.first().username}")

# Check for Google OAuth app
google_apps = SocialApp.objects.filter(provider='google')
if google_apps.exists():
    print("\n✅ Google OAuth app already configured!")
    app = google_apps.first()
    print(f"   - Name: {app.name}")
    print(f"   - Client ID: {app.client_id[:20]}...")
    print(f"   - Has Secret: {'Yes' if app.secret else 'No'}")
    
    update = input("\n   Update configuration? (y/n): ").strip().lower()
    if update != 'y':
        print("\n✅ Configuration complete! You can now use Google Sign-In.")
        sys.exit(0)
else:
    print("\n⚠️  Google OAuth app NOT configured")

print("\n" + "=" * 60)
print("STEP 1: GET GOOGLE OAUTH CREDENTIALS")
print("=" * 60)
print("\n1. Go to: https://console.cloud.google.com/")
print("2. Create a new project (or select existing)")
print("3. Go to 'APIs & Services' → 'Credentials'")
print("4. Click 'Create Credentials' → 'OAuth client ID'")
print("5. Application type: 'Web application'")
print("6. Add Authorized redirect URI:")
print("   http://127.0.0.1:8000/accounts/google/login/callback/")
print("\n7. Copy the Client ID and Client Secret shown")

print("\n" + "=" * 60)
print("STEP 2: ENTER YOUR CREDENTIALS")
print("=" * 60)

client_id = input("\nPaste your Google Client ID: ").strip()
client_secret = input("Paste your Google Client Secret: ").strip()

if not client_id or not client_secret:
    print("\n❌ Error: Both Client ID and Secret are required!")
    sys.exit(1)

print("\n" + "=" * 60)
print("STEP 3: SAVING CONFIGURATION")
print("=" * 60)

# Get or create the site
site = Site.objects.get(pk=1)
print(f"\n✅ Using site: {site.domain}")

# Create or update the social app
app, created = SocialApp.objects.update_or_create(
    provider='google',
    defaults={
        'name': 'Google OAuth',
        'client_id': client_id,
        'secret': client_secret,
    }
)

# Add the site to the app
app.sites.add(site)

if created:
    print("✅ Google OAuth app created successfully!")
else:
    print("✅ Google OAuth app updated successfully!")

print("\n" + "=" * 60)
print("✅ SETUP COMPLETE!")
print("=" * 60)
print("\nYou can now:")
print("1. Go to http://127.0.0.1:8000/")
print("2. Click 'Sign in'")
print("3. Click 'Sign in with Google'")
print("4. Sign in with your Google account")
print("\n🎉 Google OAuth is ready to use!")
