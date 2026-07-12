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

* `/kaggle competitions`
  Displays a list of currently active Kaggle competitions, including the title, category, deadline, prize information, and a direct link.

* `/kaggle competition`
  Displays detailed information about one selected competition, including its description, deadline, evaluation metric, reward, and Kaggle page.

* `/kaggle deadlines`
  Shows active competitions that are ending soon, ordered by the closest deadline.

* `/kaggle random`
  Selects one active competition at random for users who want a new project or challenge.

## Datasets

* `/kaggle datasets`
  Searches Kaggle for public datasets using a keyword or topic.

* `/kaggle dataset`
  Displays detailed information about one selected dataset, including its owner, size, description, update date, and Kaggle link.

## Notebooks

* `/kaggle notebooks`
  Searches public Kaggle notebooks using a keyword and returns relevant examples with titles, authors, and direct links.

## Notifications

* `/kaggle subscribe`
  Allows a user to subscribe to competition announcements, deadline reminders, or selected Kaggle topics.

* `/kaggle unsubscribe`
  Removes a user's existing Kaggle notification preferences.

## Utility

* `/kaggle help`
  Displays the available Kaggle commands and a short explanation of how to use each one.

* `/kaggle refresh` *(Admin)*
  Forces the bot to retrieve fresh Kaggle data and update its local cache immediately.

* `/kaggle status` *(Admin)*
  Displays the current Kaggle API connection status, last successful refresh time, cache size, and background-task status.

---

## Planned Features

* Browse active Kaggle competitions directly from Discord.
* View competitions ordered by upcoming deadline.
* Search public Kaggle datasets by keyword.
* Search public Kaggle notebooks and examples.
* Automatically announce newly detected competitions.
* Send reminders before selected competition deadlines.
* Allow users to subscribe to relevant Kaggle notifications.
* Cache API responses to reduce unnecessary requests.
* Display results using structured Discord embeds.
* Provide administrator commands for refreshing and monitoring the integration.

