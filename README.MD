# Telegram Folder Uploader

A Python program that watches a root folder and uploads files from each subfolder to its own Telegram channel.

## Features

- Creates one Telegram index channel on first run.
- Creates one Telegram channel per folder.
- Sends each folder channel invite link to the index channel.
- Uploads only new files.
- Tracks uploaded files using SQLite.
- Uses Telethon and Telegram MTProto API.

## Setup

Install dependencies:

```bash
pip install -r requirements.txt

```

## AI Usage Notice

This project was developed with the assistance of artificial intelligence tools.

AI was used to help design parts of the program structure, customize messages and improve readability.