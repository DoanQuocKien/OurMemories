# Our Memories 💕

A desktop app that uses **Telegram as a free cloud backend** — no server, no cost.

## Setup (5 minutes)

### 1. Get your Telegram credentials
1. Open Telegram → search @BotFather → /newbot
2. Copy the **API Token**
3. Send any message to your new bot
4. Visit https://api.telegram.org/bot<TOKEN>/getUpdates in your browser
5. Find your chat_id in the JSON (under esult[0].message.from.id)

### 2. Configure the app
Open pp.py and fill in lines 6-7:
`python
BOT_TOKEN = "123456789:ABC..."   # your token
CHAT_ID   = "987654321"         # your chat_id
`

### 3. Install & run (dev)
`ash
pip install -r requirements.txt
python app.py
`

### 4. Build the .exe
`ash
build.bat
# or manually:
pyinstaller --noconsole --onefile --name "OurMemories" app.py
`
The executable will be at dist\OurMemories.exe.

## How it works
| Action | What happens |
|---|---|
| App opens | Your Telegram gets "She just opened Our Memories!" |
| She uploads a photo | Posted to your Telegram chat |
| Gallery loads | Fetches photos you've sent to the bot |
