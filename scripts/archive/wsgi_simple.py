"""
Simple WSGI entry point for Railway deployment
==============================================

This version tries to import the registration form app first,
then falls back to the main app if needed.
"""
import os

# Try to load the registration form app first (simpler, no pandas)
try:
    from registration_form.app import app
    print("✅ Loaded registration form app successfully")
except ImportError as e:
    print(f"⚠️  Could not load registration form app: {e}")
    # Fallback to main app
    try:
        from app import app
        print("✅ Loaded main app successfully")
    except ImportError as e2:
        print(f"❌ Could not load any app: {e2}")
        raise e2

# This is what gunicorn will look for
application = app

if __name__ == "__main__":
    # For testing the WSGI app directly
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)