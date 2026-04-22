# Deployment Guide

## Quick Deployment (Recommended)

Run the automated deployment script:

```bash
cd /Users/nishkarshkr/Desktop/titan-concierge-bot
./deploy_to_server.sh
```

**Password:** `Akshay343402355468`

---

## Manual Deployment Steps

If the script doesn't work, follow these manual steps:

### Step 1: SSH into the server
```bash
ssh root@161.118.250.195 -p 22
# Password: Akshay343402355468
```

### Step 2: Navigate to bot directory
```bash
cd /root/concierge-bot
```

### Step 3: Pull latest changes from GitHub
```bash
git stash
git pull origin main
```

### Step 4: Stop old bot processes
```bash
pkill -9 -f "python3 bot.py"
sleep 2
```

### Step 5: Verify no bot is running
```bash
ps aux | grep "python3 bot.py" | grep -v grep
# Should show nothing
```

### Step 6: Start the bot
```bash
nohup python3 bot.py > bot.log 2>&1 & disown
```

### Step 7: Wait and check logs
```bash
sleep 5
tail -30 bot.log
```

You should see:
```
Bot started successfully!
```

### Step 8: Verify bot is running
```bash
ps aux | grep "python3 bot.py" | grep -v grep
```

Should show:
```
root  PID  ... python3 bot.py
```

---

## Useful Commands

### Check bot status
```bash
ssh root@161.118.250.195 -p 22 'ps aux | grep "python3 bot.py" | grep -v grep'
```

### View live logs
```bash
ssh root@161.118.250.195 -p 22 'tail -f /root/concierge-bot/bot.log'
```

### Restart bot
```bash
ssh root@161.118.250.195 -p 22 'pkill -f "python3 bot.py" && sleep 2 && cd /root/concierge-bot && nohup python3 bot.py > bot.log 2>&1 & disown'
```

### Stop bot
```bash
ssh root@161.118.250.195 -p 22 'pkill -f "python3 bot.py"'
```

---

## Troubleshooting

### Error: "Conflict: terminated by other getUpdates request"
This means multiple bot instances are running. Fix:
```bash
ssh root@161.118.250.195 -p 22 'pkill -9 -f "python3 bot.py" && sleep 3 && cd /root/concierge-bot && nohup python3 bot.py > bot.log 2>&1 & disown'
```

### Error: "Git pull failed"
Stash local changes first:
```bash
ssh root@161.118.250.195 -p 22 'cd /root/concierge-bot && git stash && git pull origin main'
```

### Bot not responding
1. Check if it's running: `ps aux | grep bot.py`
2. Check logs: `tail -100 bot.log`
3. Restart if needed

---

## Server Information

- **IP:** 161.118.250.195
- **Username:** root
- **Password:** Akshay343402355468
- **Port:** 22
- **Bot Directory:** /root/concierge-bot
- **Log File:** /root/concierge-bot/bot.log
- **Git Repo:** https://github.com/nishkarshk212/concierge-bot.git

---

## What Was Deployed

✅ Admin permissions disabled by default
✅ Permission panel shows all disabled initially  
✅ Save button applies permissions to Telegram
✅ Username database improvements
✅ Better user resolution system
✅ Auto-delete for admin commands
✅ Anonymous admin settings access
