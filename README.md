<!--
  README for: Telegram YouTube MP3 Downloader Bot
  GitHub: @algoanhaf
-->

<div align="center">

<h1>Telegram YouTube MP3 Downloader Bot</h1>

<p>
  A clean, fast, <b>production-ready</b> Telegram bot that converts YouTube videos into <b>MP3</b>.
</p>

<p>
  <a href="https://www.python.org/"><img alt="Python" src="https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white"></a>
  <a href="https://core.telegram.org/bots/api"><img alt="Telegram Bot API" src="https://img.shields.io/badge/Telegram-Bot%20API-26A5E4?logo=telegram&logoColor=white"></a>
  <a href="https://github.com/algoanhaf"><img alt="GitHub" src="https://img.shields.io/badge/GitHub-@algoanhaf-181717?logo=github&logoColor=white"></a>
  <img alt="Termux" src="https://img.shields.io/badge/Termux-Friendly-2E3440">
  <img alt="No aiogram" src="https://img.shields.io/badge/No-aiogram-success">
</p>

<img alt="animated divider" width="700"
     src="https://capsule-render.vercel.app/api?type=waving&color=0:7c3aed,100:2563eb&height=120&section=header&text=&fontSize=0" />

</div>

---

## ✨ What it does

This bot works in **private chats** and **groups**, supports **command-based usage** + **inline buttons**, and shows a clean **preview card** (thumbnail, title, duration) before downloading.

✅ Built for **Termux (Android)** + **Python 3.12+**  
✅ Lightweight dependencies  
✅ No aiogram • No Rust dependency

---

## ✅ Features

- Convert YouTube videos to **MP3**
- **Group command** support with reply-style response
- **Private chat** button-based download flow
- Preview card before download:
  - Thumbnail image
  - Video title
  - Duration
- Inline **Download MP3** button
- Clean temporary file handling
- Fast + stable performance
- Termux friendly

---

## 🚀 Usage

### Group Chat Usage

Send this command in a group:

```bash
/download_mp3 https://youtu.be/VIDEO_ID
```

The bot replies directly to the command message with:
- Thumbnail
- Title
- Duration
- Download MP3 button

### Private Chat Usage

1. Start the bot
2. Press **Download MP3**
3. Send a YouTube video link
4. Press **Download MP3** from the preview

---

## 🖼️ Preview Images

<div align="center">

<h3>Private Chat Preview</h3>

<img src="Screenshot_20260103_220040_Telegram.jpg" alt="Private Chat Preview" width="420" />

</div>


## 📦 Requirements

- **Python 3.12+**
- **ffmpeg**
- Telegram **Bot Token**

---

## 📱 Termux Installation (Android)

```bash
pkg update -y && pkg upgrade -y
pkg install -y python ffmpeg git
```

---

## 🧰 Python Package Installation

```bash
pip install -U pip
pip install pytelegrambotapi yt-dlp aiofiles
```

---

## 🧱 Project Setup

Clone the repository:

```bash
git clone https://github.com/algoanhaf/MP3.git
cd MP3
```

---

## ▶️ Run the Bot

```bash
python bot_mp3.py
```

### Run in background (optional)

```bash
nohup python bot_mp3.py > bot.log 2>&1 &
```

---

## 🧠 Notes (so your bot doesn’t act goofy)

- If downloads fail, confirm `ffmpeg` is installed and accessible in PATH.
- For Termux, allow storage if you need local file access:
  ```bash
  termux-setup-storage
  ```
- Keep temp files in a dedicated folder and clean up after sending.

<div align="center">

<img alt="footer" width="700"
     src="https://capsule-render.vercel.app/api?type=waving&color=0:2563eb,100:7c3aed&height=120&section=footer&text=&fontSize=0" />

<b>Made by @algoanhaf</b>

</div>
