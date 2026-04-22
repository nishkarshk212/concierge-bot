#!/bin/bash
# Deploy admin permission fixes

echo "🚀 Deploying admin permission fixes..."

# Deploy updated files
scp callback_handler.py admin_feature.py root@193.235.241.187:/var/www/titanbot/

if [ $? -eq 0 ]; then
    echo "✅ Files uploaded successfully!"
    echo ""
    echo "🔄 Restarting bot..."
    ssh root@193.235.241.187 'cd /var/www/titanbot && pkill -f "python3 bot.py" && sleep 2 && nohup python3 bot.py > bot.log 2>&1 & sleep 2 && ps aux | grep "python3 bot.py" | grep -v grep'
    
    echo ""
    echo "✅ Deployment complete!"
    echo ""
    echo "📋 Changes deployed:"
    echo "  ✓ /admin command now promotes with ALL permissions disabled"
    echo "  ✓ Permission panel shows all permissions as disabled by default"
    echo "  ✓ Toggling permissions updates them in cache"
    echo "  ✓ Save button applies permissions to Telegram group settings"
    echo "  ✓ Clear instructions: 'All permissions disabled by default'"
    echo ""
    echo "🎯 New Behavior:"
    echo "  1. /admin @user → Promotes with NO permissions"
    echo "  2. Click '🕹 Permissions' → All toggles show ❌ (disabled)"
    echo "  3. Enable desired permissions (toggle to ✅)"
    echo "  4. Click 'Save ✔️' → Updates Telegram admin settings"
    echo "  5. Permissions are immediately applied to the group!"
else
    echo "❌ Upload failed! Check server connectivity."
fi
