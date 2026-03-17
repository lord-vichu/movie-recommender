"""
Quick setup script for CINE-M-AURA Django app
Run this after activating your virtual environment
"""
import os
import sys

def run_command(command):
    """Run a shell command"""
    print(f"\n>>> Running: {command}")
    result = os.system(command)
    if result != 0:
        print(f"Warning: Command returned non-zero exit code: {result}")
    return result

def main():
    print("=" * 60)
    print("CINE-M-AURA Django App - Setup Script")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists('manage.py'):
        print("\n❌ Error: manage.py not found!")
        print("Please run this script from the project root directory.")
        sys.exit(1)
    
    print("\n✅ Found manage.py")
    
    # Run migrations
    print("\n📦 Creating database migrations...")
    run_command("python manage.py makemigrations")
    
    print("\n📦 Applying database migrations...")
    run_command("python manage.py migrate")
    
    # Create superuser prompt
    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Create a superuser (optional):")
    print("   python manage.py createsuperuser")
    print("\n2. Run the development server:")
    print("   python manage.py runserver")
    print("\n3. Open your browser to: http://127.0.0.1:8000/")
    print("\n4. Access admin panel at: http://127.0.0.1:8000/admin/")
    print("=" * 60)

if __name__ == '__main__':
    main()
