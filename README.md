# 🎵 ShizuMusic
<div align="center">

<img src="https://files.catbox.moe/f084wg.png" alt="ShizuMusic" width="100%">

**First open-source Telegram VC music bot.**
Fast • Smooth • Powerful — runs free on Render, Koyeb, Railway & Heroku.

Powered by [Pyrogram](https://github.com/pyrogram/pyrogram), [Py-TgCalls](https://github.com/pytgcalls/pytgcalls) & [Richgram](https://github.com/Badmunda05/richgram)

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![Pyrogram](https://img.shields.io/badge/Pyrogram-2.x-00BFFF?style=flat-square)
![PyTgCalls](https://img.shields.io/badge/Py--TgCalls-VC-6A5ACD?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

</div>

---

## ✨ Features

- 🎵 High quality VC audio & video streaming
- 🔁 Queue system with auto-play
- ⏯ Pause, resume, skip, stop & seek controls
- 🎚 Speed and bass boost effects
- 📂 Personal playlists
- 📡 Channel play
- 🌐 Multi-language (English, Hindi, Punjabi)
- 🔒 Admin-only controls, owner block lists & broadcast

---

## 🚀 Deploy

<div align="center">

[![Heroku](https://img.shields.io/badge/Deploy-Heroku-430098?style=for-the-badge&logo=heroku&logoColor=white)](https://dashboard.heroku.com/new?template=https://github.com/Badmunda05/ShizuMusic)
[![Koyeb](https://img.shields.io/badge/Deploy-Koyeb-121212?style=for-the-badge&logo=koyeb&logoColor=white)](https://app.koyeb.com/deploy?type=git&repository=github.com/Badmunda05/ShizuMusic&branch=main&name=shizumusic)
[![Render](https://img.shields.io/badge/Deploy-Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)](https://render.com/deploy?repo=https://github.com/Badmunda05/ShizuMusic)
[![Railway](https://img.shields.io/badge/Deploy-Railway-0B0D0E?style=for-the-badge&logo=railway&logoColor=white)](https://railway.app/new/template?template=https://github.com/Badmunda05/ShizuMusic)

</div>

### 🖥️ VPS (Ubuntu 20.04+ / Debian 11+)

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip git ffmpeg screen

git clone https://github.com/Badmunda05/ShizuMusic
cd ShizuMusic
pip3 install -r requirements.txt

nano .env                      # fill in the variables below
screen -S shizu                # keep it running after closing terminal
python3 -m ShizuMusic          # detach: Ctrl+A then D
```

---

## 🔑 Environment Variables

Create a `.env` file in the project root.

### Required

```env
API_ID=             # my.telegram.org
API_HASH=           # my.telegram.org
BOT_TOKEN=          # @BotFather
OWNER_ID=           # your Telegram user ID
STRING_SESSION=     # Pyrogram session of the assistant account
MONGO_DB_URL=       # MongoDB connection string
YT_API_URL=         # external API url for downloads
YT_API_KEY=         # external API key
```

### Optional

```env
LOGGER_ID=          # log group/channel ID
BOT_NAME=           # default: Shizu Music
BOT_LINK=           # your bot's t.me link
SUPPORT_GROUP=      # support group link
UPDATES_CHANNEL=    # updates channel link
PING_IMG_URL=       # image shown in /ping
SESSION_NAME=       # default: ShizuMusic
PORT=               # default: 10000 (Render / Koyeb)
```

> ⚙️ Limits like `MAX_DURATION_SECONDS` (30 min), `QUEUE_LIMIT` (20), `COOLDOWN` (10s) and playlist limits are set directly in `config.py`.

| Get this | From |
|---|---|
| `API_ID` / `API_HASH` | [my.telegram.org](https://my.telegram.org) |
| `BOT_TOKEN` | [@BotFather](https://t.me/BotFather) |
| `STRING_SESSION` | [telegram.tools](https://telegram.tools/session-string-generator#pyrogram) |
| `MONGO_DB_URL` | [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register) (free) |

---
### 🎧 Playback

| Command | What it does |
|---|---|
| `/play <name or link>` | Play audio in VC (or reply to an audio/video file) |
| `/vplay <name or link>` | Play video in VC |
| `/playforce <name or link>` | Play now, keep the queue |
| `/pause` | Pause the stream |
| `/resume` | Resume the stream |
| `/skip` | Skip to next song |
| `/stop` · `/end` | Stop and clear the queue |
| `/clear` | Clear the queue |
| `/autoplay` | Auto-play related songs on/off |
| `/thumbnail on` · `off` | Show or hide the song thumbnail |

### ⏩ Seek & Effects

| Command | What it does |
|---|---|
| `/seek 30` | Forward 30 seconds |
| `/seekback 30` | Backward 30 seconds |
| `/speed 1.5` | Set speed (0.25 – 4.0) |
| `/speedreset` | Back to normal speed |
| `/bass 10` | Bass boost (1 – 20 dB) |
| `/bassoff` | Remove bass boost |
| `/effecton` · `/effectoff` | Apply effects to all songs / manual mode |
| `/effects` | Show effect settings |

### 📂 Playlists

| Command | What it does |
|---|---|
| `/pcreate` | Create a playlist |
| `/padd` | Add a song to a playlist |
| `/premove` | Remove a song from a playlist |
| `/pview` | View your playlists |
| `/pplay` | Play a playlist |
| `/pdelete` | Delete a playlist |

### 📡 Channel

| Command | What it does |
|---|---|
| `/addchannel` · `/setchannel` | Link a channel for channel play |
| `/delchannel` · `/removechannel` | Unlink the channel |
| `/cplay` · `/cvplay` | Play audio / video in the channel VC |
| `/cpause` `/cresume` `/cskip` `/cstop` | Control the channel stream |

### ℹ️ General

| Command | What it does |
|---|---|
| `/start` | Start the bot |
| `/help` | Help menu |
| `/ping` | Bot status, uptime, RAM & CPU |
| `/id` | Get chat / user ID |
| `/language` · `/lang` | Change bot language |
| `/repo` | Source code |

### 👑 Owner Only

| Command | What it does |
|---|---|
| `/stats` | Bot & database stats |
| `/speedtest` · `/spt` | Server speed test |
| `/broadcast` · `/gcast` | Broadcast a message. Flags: `-pin` `-pinloud` `-nogroup` `-user` |
| `/logger` | Check or toggle logging |
| `/gblock` · `/gunblock` | Block / unblock a group |
| `/ublock` · `/uunblock` | Block / unblock a user |
| `/blocklist` | View blocked chats & users |
| `/reboot` | Restart the bot |

---

## 💬 Community & Support

<p align="center">
  <a href="https://t.me/PBXCHATS">
    <img src="https://img.shields.io/badge/Support_Group-Telegram-0088cc?style=for-the-badge&logo=telegram&logoColor=white" />
  </a>
  <a href="https://t.me/PBX_UPDATE">
    <img src="https://img.shields.io/badge/Updates_Channel-Telegram-6A5ACD?style=for-the-badge&logo=telegram&logoColor=white" />
  </a>
  <a href="mailto:munda.bad1322@gmail.com">
    <img src="https://img.shields.io/badge/Contact-Email-D14836?style=for-the-badge&logo=gmail&logoColor=white" />
    <a href="https://t.me/Badmundaxd">
    <img src="https://img.shields.io/badge/Contact_Owner-Telegram-4CAF50?style=for-the-badge&logo=telegram&logoColor=white" />
  </a>
  </a>
</p>

---

## 🙏 Credits

- [**Richgram**](https://github.com/Badmunda05/richgram) — rich message formatting library used for the bot's styled replies.
- [Pyrogram](https://github.com/pyrogram/pyrogram) — Telegram MTProto framework.
- [Py-TgCalls](https://github.com/pytgcalls/pytgcalls) — voice chat streaming.

---

## 📜 License

Licensed under the [MIT License](LICENSE) © 2026 ShizuMusic™

<div align="center">

**Made with ❤️ by PBX — ShizuMusic™**

[![Stars](https://img.shields.io/github/stars/Badmunda05/ShizuMusic?style=for-the-badge&color=yellow)](https://github.com/Badmunda05/ShizuMusic/stargazers)
[![Forks](https://img.shields.io/github/forks/Badmunda05/ShizuMusic?style=for-the-badge&color=blue)](https://github.com/Badmunda05/ShizuMusic/network/members)

</div>
