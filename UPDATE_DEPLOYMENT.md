# Update Deployment Guide

## How to Add Update Notifications When Deploying New Features

### Step 1: Update the features list in bot.py
Open `bot.py` and find the `post_init` function (around line 260).

Update the `recent_updates` list with your new features:

```python
recent_updates = [
    "✅ Your new feature 1 description here",
    "✅ Your new feature 2 description here",
    "✅ Your bug fix description here",
    # Add more features as needed
]
```

### Step 2: Commit and push to Git
```bash
git add .
git commit -m "Your commit message describing the update"
git push
```

### Step 3: Pull and restart on server
```bash
ssh root@161.118.250.195 -p 22
cd /root/concierge-bot
git pull
systemctl restart titanic-bot
```

### Step 4: Check log group
The bot will automatically send an update notification to the log group with:
- Bot name
- Service name (titanic-bot)
- Date and time of update
- List of all new features/changes
- Deployment status

---

## Example Update Notification Message

```
🔄 BOT UPDATE DEPLOYED

❅─────✧❅✦❅✧─────❅

🤖 BOT: @YourBotName
🖥️ SERVICE: titanic-bot
📅 DATE: 21/04/2026 20:15:30

📦 UPDATE DETAILS:
  1. ✅ Free permission panel toggle buttons - green check (allowed), red cross (not allowed)
  2. ✅ Save button stability in free permission panel - no longer changes to Back button
  3. ✅ User-specific permission tracking in free command panel
  4. ✅ Update notification system - logs all updates to log group with service name

✅ STATUS: Successfully deployed and running!
🚀 All systems operational!
```

---

## Service Information
- **Service Name:** titanic-bot
- **Server IP:** 161.118.250.195
- **Port:** 22
- **Username:** root
- **Bot Directory:** /root/concierge-bot

## Useful Commands

Check service status:
```bash
systemctl status titanic-bot
```

View service logs:
```bash
journalctl -u titanic-bot -f
```

Restart service:
```bash
systemctl restart titanic-bot
```

Stop service:
```bash
systemctl stop titanic-bot
```

Start service:
```bash
systemctl start titanic-bot
```
