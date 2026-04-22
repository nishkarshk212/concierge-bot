#!/bin/bash
# Deploy username database method from titanic-saver repo

echo "🚀 Deploying username database improvements..."

# Deploy updated files
scp database.py admin_feature.py bot.py root@193.235.241.187:/var/www/titanbot/

if [ $? -eq 0 ]; then
    echo "✅ Files uploaded successfully!"
    echo ""
    echo "🔄 Restarting bot..."
    ssh root@193.235.241.187 'cd /var/www/titanbot && pkill -f "python3 bot.py" && sleep 2 && nohup python3 bot.py > bot.log 2>&1 & sleep 2 && ps aux | grep "python3 bot.py" | grep -v grep'
    
    echo ""
    echo "✅ Deployment complete!"
    echo ""
    echo "📋 Changes deployed:"
    echo "  ✓ Username database now stores user_id AND first_name"
    echo "  ✓ get_user_id_by_username() returns (user_id, user_name) tuple"
    echo "  ✓ resolve_user() simplified to match titanic-saver approach"
    echo "  ✓ Users automatically cached with first_name for better display"
    echo "  ✓ Cleaner, faster username resolution"
    echo ""
    echo "🔍 Key improvements:"
    echo "  • Database-first approach (like titanic-saver)"
    echo "  • Simplified resolution: DB → get_chat API → error"
    echo "  • Automatic user caching with full names"
    echo "  • Better error messages"
else
    echo "❌ Upload failed! Check server connectivity."
fi
