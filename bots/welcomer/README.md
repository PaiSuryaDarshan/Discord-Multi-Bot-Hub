# Discord ID Welcomer

<p align="center">
  <img src="../../assets/banner_welcomer.png" alt="Discord Identity Card Bot Banner" width="100%">
</p>

Automatically generates a permanent identity card for new or existing members based on their Discord roles.

Administrators simply run:

```text
!welcome @member
```

The bot converts structured role names into natural-language profile statements and posts a formatted embed in the server's `#welcome` channel.

---

## Features

- 📇 Generates permanent member ID cards
- 🏷️ Converts role categories into readable profile statements
- 🎨 Uses the member's avatar and role colour
- 🔒 Administrator-only command
- 📍 Automatically posts to `#welcome`
- 🧩 Supports both structured and unstructured roles

---

## Role Format

Structured roles use:

```text
Category:Value
```

Example:

```text
Career_Goal:Quant Research
Programming_Language:Python
Research_Interest:Machine Learning
Education:Master's
Region:Europe
```

Unknown categories are still supported using a generic sentence.

---

## Example

```text
Welcome — Member ID Card

Hi. I am @Surya

Career Goal
I aspire to work in Quant Research.

Programming Language
I program in Python.

Education
My education level is Master's.
```

---

## Bot Folder

```text
welcomer/
├── bot.py
├── __init__.py
└── README.md
```

The bot is started by the repository's central `main.py` launcher alongside the other Discord bots.

---

Licensed under the MIT License.