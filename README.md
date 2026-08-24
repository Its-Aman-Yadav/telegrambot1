# 🎬 Telegram Force-Subscription Movie Bot

A high-performance Telegram Bot built with Python (`python-telegram-bot`) that forces users to join your Telegram Channel before they can search, access, or download movies.

---

## ✨ Features

- 🔒 **Force Channel Subscription**: Automatically checks if a user is subscribed to your channel via `getChatMember`.
- 🔄 **Real-Time Verification Button**: "I Have Joined / Try Again" button for instant re-checking without re-typing.
- 🎬 **Movie Search & Catalog**: Users can search for movies by name directly in the chat or browse the latest additions.
- 🔗 **Deep-Linking Support**: Generate shareable links like `https://t.me/YourBot?start=movie_code`. When users click, they are asked to join the channel before receiving the movie.
- 📁 **Admin Media Forwarding**: Send or forward any video/document directly to the bot to store it and generate deep-links automatically.
- 📊 **Admin Tools**:
  - `/addmovie <Title> | <Download_URL> | <Description>`
  - `/stats` (View total users & movies)
  - `/broadcast <Message>` (Send announcements to all bot users)
- 💾 **SQLite Storage**: Zero-configuration local database for users and movies.

---

## 🚀 Setup Guide

### 1. Prerequisites
- Python 3.10 or higher
- A Telegram account

### 2. Create Your Telegram Bot
1. Open Telegram and search for [@BotFather](https://t.me/BotFather).
2. Send `/newbot` and follow the prompts to get your **Bot Token**.

### 3. Add Bot as Channel Administrator
> [!IMPORTANT]
> The bot **must** be an **Administrator** in your channel so that it can verify if users have joined!
1. Go to your Telegram channel settings.
2. Click **Administrators** > **Add Administrator**.
3. Search for your bot username and give it standard admin permissions (Invite Users / Add Members).

### 4. Installation

Clone or navigate to the project directory:
```bash
cd /Users/aman/Desktop/SideProjects/moviesbot
```

Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate
```

Install the dependencies:
```bash
pip install -r requirements.txt
```

### 5. Configuration

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Open `.env` and fill in your details:
```env
BOT_TOKEN=123456789:ABCDefGhIjKlmnOpQrStUvWxYz
CHANNEL_ID=@YourChannelUsername
CHANNEL_INVITE_LINK=https://t.me/YourChannelUsername
ADMIN_ID=1234567890
```

> **How to get your numeric `ADMIN_ID`:** Send `/start` to [@userinfobot](https://t.me/userinfobot) on Telegram to get your user ID.

---

## ▶️ Running the Bot

Start the bot:
```bash
python3 bot.py
```

---

## 💡 How to Add Movies

### Method 1: Forwarding Video/File directly (Fastest)
1. As the admin, send or forward any video or document file directly to the bot.
2. The bot will automatically save it and give you a deep-link (e.g. `https://t.me/YourBot?start=inception_123`).

### Method 2: `/addmovie` Command
Run the command in your chat with the bot:
```
/addmovie Interstellar (2014) | https://example.com/dl/interstellar.mp4 | Epic sci-fi film directed by Christopher Nolan
```

---

## 🛠️ Bot Commands

| Command | Permission | Description |
| :--- | :--- | :--- |
| `/start` | Public | Starts the bot and checks channel membership |
| `/start <movie_code>` | Public | Deep-link to deliver a specific movie after channel verification |
| `/addmovie` | Admin | Adds a movie link manually |
| `/stats` | Admin | Displays total users and catalog count |
| `/broadcast <msg>` | Admin | Broadcasts a text message to all users |
