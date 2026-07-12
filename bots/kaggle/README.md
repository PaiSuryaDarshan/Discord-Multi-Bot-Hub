# Kaggle Bot

A Discord bot providing quick access to Kaggle competitions, datasets, notebooks, and reminders without leaving Discord.

---

## Repository Structure

```text
bots/
└── kaggle/
    ├── __init__.py
    ├── cog.py
    ├── client.py
    ├── competitions.py
    ├── datasets.py
    ├── notebooks.py
    ├── alerts.py
    ├── tasks.py
    ├── embeds.py
    ├── models.py
    ├── config.py
    ├── cache.py
    ├── utils.py
    ├── README.md
    └── data/
        ├── competitions_cache.json
        ├── datasets_cache.json
        └── announced_items.json
```

| File | Purpose |
|------|---------|
| `__init__.py` | Package initialisation. |
| `cog.py` | Registers all slash commands. |
| `client.py` | Handles Kaggle API authentication and requests. |
| `competitions.py` | Competition retrieval and filtering logic. |
| `datasets.py` | Dataset search and metadata retrieval. |
| `notebooks.py` | Notebook (Kernel) search functionality. |
| `alerts.py` | Automatic competition and deadline notifications. |
| `tasks.py` | Scheduled background refresh tasks. |
| `embeds.py` | Discord embed formatting. |
| `models.py` | Shared data models and objects. |
| `config.py` | Configuration constants and settings. |
| `cache.py` | Local cache management. |
| `utils.py` | General helper functions. |
| `data/competitions_cache.json` | Cached competitions. |
| `data/datasets_cache.json` | Cached datasets. |
| `data/announced_items.json` | Tracks previously announced competitions. |

---

# Initial Command Ideas

## Competitions

- `/kaggle competitions`
- `/kaggle competition`
- `/kaggle deadlines`
- `/kaggle random`

## Datasets

- `/kaggle datasets`
- `/kaggle dataset`

## Notebooks

- `/kaggle notebooks`

## Notifications

- `/kaggle subscribe`
- `/kaggle unsubscribe`

## Utility

- `/kaggle help`
- `/kaggle refresh` *(Admin)*
- `/kaggle status` *(Admin)*

---

## Planned Features

- Browse active competitions
- View upcoming competition deadlines
- Search public datasets
- Search Kaggle notebooks
- Automatic competition announcements
- Deadline reminders
- Local caching to minimise API requests
- Rich Discord embeds
- Administrator refresh controls