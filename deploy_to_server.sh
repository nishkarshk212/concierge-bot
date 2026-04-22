#!/bin/bash
# Deploy bot updates from GitHub repository to server

echo "======================================"
echo "🚀 Bot Deployment Script"
echo "======================================"
echo ""

SERVER_IP="161.118.250.195"
SERVER_USER="root"
SERVER_PORT="22"
BOT_DIR="/root/concierge-bot"

echo "📋 Step 1: Pulling latest changes from GitHub..."
ssh -p $SERVER_PORT ${SERVER_USER}@${SERVER_IP} "cd ${BOT_DIR} && git stash && git pull origin main"

if [ $? -eq 0 ]; then
    echo "✅ Code updated successfully!"
else
    echo "❌ Failed to update code!"
    exit 1
fi

echo ""
echo "📋 Step 2: Stopping old bot processes..."
ssh -p $SERVER_PORT ${SERVER_USER}@${SERVER_IP} "pkill -9 -f 'python3 bot.py' 2>/dev/null; sleep 2; echo '✅ Old processes stopped'"

echo ""
echo "📋 Step 3: Starting bot..."
ssh -p $SERVER_PORT ${SERVER_USER}@${SERVER_IP} "cd ${BOT_DIR} && nohup python3 bot.py > bot.log 2>&1 & disown"

echo ""
echo "📋 Step 4: Waiting 5 seconds for bot to start..."
sleep 5

echo ""
echo "📋 Step 5: Checking if bot is running..."
BOT_PID=$(ssh -p $SERVER_PORT ${SERVER_USER}@${SERVER_IP} "pgrep -f 'python3 bot.py' | head -1")

if [ -n "$BOT_PID" ]; then
    echo "✅ Bot is running! (PID: $BOT_PID)"
    echo ""
    echo "📋 Step 6: Recent bot logs:"
    ssh -p $SERVER_PORT ${SERVER_USER}@${SERVER_IP} "cd ${BOT_DIR} && tail -10 bot.log"
    echo ""
    echo "======================================"
    echo "✅ Deployment Complete!"
    echo "======================================"
    echo ""
    echo "📝 Summary of changes deployed:"
    echo "  ✓ Admin permissions disabled by default"
    echo "  ✓ Permission panel shows all disabled"
    echo "  ✓ Save button applies to Telegram"
    echo "  ✓ Username database improvements"
    echo "  ✓ Better user resolution"
    echo ""
    echo "🔍 To check bot status:"
    echo "  ssh -p $SERVER_PORT ${SERVER_USER}@${SERVER_IP} 'cd ${BOT_DIR} && tail -f bot.log'"
    echo ""
    echo "🛑 To stop bot:"
    echo "  ssh -p $SERVER_PORT ${SERVER_USER}@${SERVER_IP} 'pkill -f \"python3 bot.py\"'"
else
    echo "❌ Bot failed to start!"
    echo ""
    echo "📋 Check logs:"
    ssh -p $SERVER_PORT ${SERVER_USER}@${SERVER_IP} "cd ${BOT_DIR} && tail -30 bot.log"
    exit 1
fi
