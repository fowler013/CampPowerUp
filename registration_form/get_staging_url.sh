#!/bin/bash

echo "🚂 Railway Staging Database URL Setup"
echo "====================================="
echo ""
echo "To get your Railway staging DATABASE_URL:"
echo ""
echo "1. 🌐 Visit: https://railway.app/dashboard"
echo "2. 📂 Select your Camp Power-Up project"
echo "3. 🔧 Go to Variables tab"
echo "4. 📋 Copy the DATABASE_URL value"
echo "5. ✏️  Edit .env.staging and paste it after DATABASE_URL="
echo ""
echo "Example format:"
echo "DATABASE_URL=postgresql://user:pass@region.railway.app:5432/railway"
echo ""
echo "Then run: ./use_staging.sh"
echo ""
echo "🔍 Your current staging config:"
if [ -f ".env.staging" ]; then
    echo "----"
    cat .env.staging | grep -E "DATABASE_URL|ENVIRONMENT"
    echo "----"
else
    echo "❌ .env.staging not found"
fi