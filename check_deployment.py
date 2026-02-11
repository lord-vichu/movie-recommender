"""
Pre-Deployment Checklist Script
Run this before deploying to check if everything is configured correctly
"""

import os
import sys
import django

print("=" * 70)
print(" 🚀 DEPLOYMENT READINESS CHECKER")
print("=" * 70)

# Check if we're in the right directory
if not os.path.exists('manage.py'):
    print("\n❌ Error: manage.py not found!")
    print("   Please run this script from the movie_recommender directory")
    sys.exit(1)

print("\n✅ Found manage.py")

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movie_recommender.settings')
django.setup()

from django.conf import settings
from django.core.management import call_command
from django.core.exceptions import ImproperlyConfigured

issues = []
warnings = []

print("\n" + "=" * 70)
print(" 📋 CONFIGURATION CHECKS")
print("=" * 70)

# Check DEBUG setting
print("\n[1/10] Checking DEBUG setting...")
if settings.DEBUG:
    warnings.append("⚠️  DEBUG is True (should be False in production)")
    print("     ⚠️  DEBUG=True (set to False for production)")
else:
    print("     ✅ DEBUG=False")

# Check SECRET_KEY
print("\n[2/10] Checking SECRET_KEY...")
if 'django-insecure' in settings.SECRET_KEY:
    issues.append("❌ Using default SECRET_KEY")
    print("     ❌ Still using default SECRET_KEY")
    print("     → Generate new key at: https://djecrety.ir/")
else:
    print("     ✅ Custom SECRET_KEY configured")

# Check ALLOWED_HOSTS
print("\n[3/10] Checking ALLOWED_HOSTS...")
if not settings.ALLOWED_HOSTS or settings.ALLOWED_HOSTS == ['*']:
    warnings.append("⚠️  ALLOWED_HOSTS not configured")
    print("     ⚠️  ALLOWED_HOSTS needs configuration")
else:
    print(f"     ✅ ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")

# Check static files
print("\n[4/10] Checking static files configuration...")
if hasattr(settings, 'STATIC_ROOT'):
    print(f"     ✅ STATIC_ROOT: {settings.STATIC_ROOT}")
else:
    issues.append("❌ STATIC_ROOT not configured")
    print("     ❌ STATIC_ROOT not set")

if hasattr(settings, 'STATICFILES_STORAGE'):
    print(f"     ✅ STATICFILES_STORAGE configured")
else:
    warnings.append("⚠️  STATICFILES_STORAGE not configured")
    print("     ⚠️  STATICFILES_STORAGE not set")

# Check middleware
print("\n[5/10] Checking middleware...")
middleware_list = [m for m in settings.MIDDLEWARE]
if 'whitenoise.middleware.WhiteNoiseMiddleware' in middleware_list:
    print("     ✅ WhiteNoise middleware configured")
else:
    issues.append("❌ WhiteNoise middleware missing")
    print("     ❌ WhiteNoise middleware not found")

# Check installed apps
print("\n[6/10] Checking installed apps...")
required_apps = ['django.contrib.staticfiles', 'allauth', 'movies']
for app in required_apps:
    if app in settings.INSTALLED_APPS:
        print(f"     ✅ {app}")
    else:
        issues.append(f"❌ {app} missing from INSTALLED_APPS")
        print(f"     ❌ {app} not found")

# Check database
print("\n[7/10] Checking database...")
try:
    from django.db import connection
    connection.ensure_connection()
    print("     ✅ Database connection successful")
except Exception as e:
    issues.append(f"❌ Database connection failed: {str(e)}")
    print(f"     ❌ Database error: {str(e)}")

# Check migrations
print("\n[8/10] Checking migrations...")
try:
    from io import StringIO
    out = StringIO()
    call_command('showmigrations', '--plan', stdout=out, stderr=StringIO())
    output = out.getvalue()
    if '[X]' in output or output.strip():
        print("     ✅ Migrations appear to be applied")
    else:
        warnings.append("⚠️  No migrations applied")
        print("     ⚠️  Run: python manage.py migrate")
except Exception as e:
    warnings.append(f"⚠️  Could not check migrations: {str(e)}")
    print(f"     ⚠️  Migration check failed: {str(e)}")

# Check requirements.txt
print("\n[9/10] Checking requirements.txt...")
if os.path.exists('requirements.txt'):
    with open('requirements.txt', 'r') as f:
        requirements = f.read()
    
    required_packages = ['Django', 'gunicorn', 'whitenoise']
    for pkg in required_packages:
        if pkg.lower() in requirements.lower():
            print(f"     ✅ {pkg}")
        else:
            issues.append(f"❌ {pkg} not in requirements.txt")
            print(f"     ❌ {pkg} missing")
else:
    issues.append("❌ requirements.txt not found")
    print("     ❌ requirements.txt not found")

# Check Procfile
print("\n[10/10] Checking deployment files...")
if os.path.exists('Procfile'):
    print("     ✅ Procfile exists")
else:
    warnings.append("⚠️  Procfile missing (needed for Heroku/Render)")
    print("     ⚠️  Procfile not found")

if os.path.exists('runtime.txt'):
    print("     ✅ runtime.txt exists")
else:
    warnings.append("⚠️  runtime.txt missing")
    print("     ⚠️  runtime.txt not found")

# Summary
print("\n" + "=" * 70)
print(" 📊 SUMMARY")
print("=" * 70)

if not issues and not warnings:
    print("\n🎉 ALL CHECKS PASSED!")
    print("   Your app is ready for deployment!")
elif not issues:
    print(f"\n✅ No critical issues found")
    print(f"⚠️  {len(warnings)} warning(s) found (optional fixes)")
else:
    print(f"\n❌ Found {len(issues)} critical issue(s)")
    print(f"⚠️  Found {len(warnings)} warning(s)")

if issues:
    print("\n" + "=" * 70)
    print(" ❌ CRITICAL ISSUES (Must Fix)")
    print("=" * 70)
    for issue in issues:
        print(f"  {issue}")

if warnings:
    print("\n" + "=" * 70)
    print(" ⚠️  WARNINGS (Recommended Fixes)")
    print("=" * 70)
    for warning in warnings:
        print(f"  {warning}")

# Deployment recommendations
print("\n" + "=" * 70)
print(" 🎯 RECOMMENDED ACTIONS")
print("=" * 70)

if issues:
    print("\n1. Fix all critical issues listed above")
    print("2. Run this script again to verify fixes")
    print("3. Then proceed with deployment")
else:
    print("\n✅ Your app is ready to deploy!")
    print("\nNext steps:")
    print("1. Choose a hosting platform (see DEPLOYMENT.md)")
    print("2. Set environment variables on your platform:")
    print("   - DEBUG=False")
    print("   - DJANGO_SECRET_KEY=<new-secret-key>")
    print("   - ALLOWED_HOSTS=<your-domain>")
    print("   - TMDB_API_KEY=3658d16dd2e533776cb67b728a8f5a3c")
    print("   - GOOGLE_OAUTH_CLIENT_ID=<your-client-id>")
    print("   - GOOGLE_OAUTH_CLIENT_SECRET=<your-secret>")
    print("3. Deploy!")
    print("\n📖 Full guide: DEPLOYMENT.md")

print("\n" + "=" * 70)
print(" For detailed deployment instructions, see: DEPLOYMENT.md")
print("=" * 70)
