#!/bin/bash

echo "🏕️ Camp Power-Up Staging Configuration Setup"
echo "============================================="

# Check if staging env file exists
if [ ! -f ".env.staging" ]; then
    echo "❌ .env.staging file not found!"
    echo "Please create .env.staging with your Railway staging DATABASE_URL"
    exit 1
fi

# Copy staging environment
cp .env.staging .env

echo "✅ Switched to staging environment"
echo ""
echo "📝 To configure for your Railway staging:"
echo "1. Get your staging DATABASE_URL from Railway dashboard"
echo "2. Edit .env.staging and add: DATABASE_URL=your_staging_url"
echo "3. Run this script again"
echo ""
echo "🚀 To start the app in staging mode:"
echo "   python app.py"
echo ""
echo "🔍 To verify staging connection:"
echo "   python -c 'from database_config import DB_CONFIG; print(f\"Production mode: {DB_CONFIG[\"is_production\"]}\")"'"