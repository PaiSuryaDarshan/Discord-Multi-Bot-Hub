# 📚 Bookworm

<p align="center">
  <img src="../../assets/banner_bookworm.png" alt="Discord Identity Card Bot Banner" width="100%">
</p>

A lightweight Discord bot that recommends books using the **Hardcover GraphQL API**.

Bookworm allows users to search Hardcover's catalogue directly from Discord with live autocomplete and returns rich embeds containing book metadata such as ratings, authors, genres, descriptions, and cover artwork.

---

## Features

- 🔍 Live book search with Discord autocomplete
- 📖 Rich book information embeds
- ⭐ Ratings and review counts
- 🏷️ Genres and moods
- 🖼️ Cover images
- 📅 Release information
- 🔗 Direct links to Hardcover
- 🚀 Lightweight and easy to deploy

---

## Project Structure

```text
bot.py         Discord slash commands
hardcover.py   Hardcover GraphQL client
embeds.py      Discord embed generation
```

---

## Environment Variables

Create a `.env` file containing:

```env
DISCORD_TOKEN=your_discord_bot_token
HARDCOVER_API_TOKEN=your_hardcover_api_token
```

---

## Installation

```bash
pip install -r requirements.txt
```

Run the bot:

```bash
python bot.py
```

---

## Command

```text
/recommend_book
```

Start typing a book title or author, select a suggestion, and Bookworm will retrieve the complete book information from Hardcover.

---

## Notes

- This bot is intended for private Discord communities.
- Book data is provided by the Hardcover API.
- Only configured Discord channels are permitted to use the bot.
- No database or persistent storage is required.
```
