#!/bin/bash
# 🚀 Camp Power-Up Deployment Script
# Quickly deploy changes and verify the website is working

echo "🏕️ Camp Power-Up Deployment"
echo "=========================="

# Check if we're in the right directory
if [ ! -f "registration_form/app.py" ]; then
    echo "❌ Error: Run this script from the CampPowerUp directory"
    exit 1
fi

# Check for uncommitted changes
if ! git diff --quiet; then
    echo "📝 Uncommitted changes found. Committing..."
    git add .
    read -p "Enter commit message: " commit_msg
    git commit -m "$commit_msg"
fi

# Push to trigger deployment
echo "🚀 Pushing to GitHub (triggers automatic Railway deployment)..."
git push origin main

echo ""
echo "✅ Changes pushed to GitHub!"
echo "🔄 Railway will automatically deploy in 2-3 minutes"
echo ""
echo "🔗 Your live website:"
echo "   Registration Form: https://camppowerup-production.up.railway.app/"
echo "   Admin Dashboard:   https://camppowerup-production.up.railway.app/admin"
echo ""
echo "📊 Monitor deployment at: https://railway.app"
echo ""

# Wait a moment then test the website
echo "⏳ Waiting 30 seconds, then testing website..."
sleep 30

echo "🧪 Testing website..."
if curl -s -o /dev/null -w "%{http_code}" https://camppowerup-production.up.railway.app/ | grep -q "200"; then
    echo "✅ Website is responding!"
else
    echo "⚠️  Website might still be deploying. Check Railway dashboard if issues persist."
fi

echo ""
echo "🎉 Deployment complete!"