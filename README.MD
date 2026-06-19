# TeleSync

TeleSync is a desktop application that syncs local folders to Telegram channels.

Each selected main folder gets its own Telegram index channel. Each subfolder inside that main folder gets its own Telegram upload channel. When a new folder channel is created, TeleSync sends its invite link to the corresponding index channel.

## Features

* Cross-platform desktop GUI for Windows and Linux.
* Telegram login through the GUI.
* Supports multiple main folders.
* Creates one Telegram index channel per main folder.
* Creates one Telegram channel per subfolder.
* Uploads only new files.
* Stores each main folder database inside that folder.
* Tracks uploaded files with SQLite.
* Uses Telethon and the Telegram API.

## How TeleSync Organizes Folders

Example local structure:

```text
Documents/
├── Work/
│   ├── file1.pdf
│   └── file2.docx
├── Photos/
│   └── image.png
└── .telesync/
    └── telesync.db
```

Telegram structure created by TeleSync:

```text
TeleSync - Documents      <- index channel for the main folder
Work                      <- upload channel for Documents/Work
Photos                    <- upload channel for Documents/Photos
```

The `.telesync/telesync.db` file stores the Telegram channel information and the list of files already uploaded for that main folder.

## Requirements

* Python 3.10 or newer
* A Telegram account
* Telegram API credentials:

  * `API_ID`
  * `API_HASH`

## Getting Your Telegram API_ID and API_HASH

TeleSync uses the Telegram API through Telethon. To use it, you need to create a Telegram application and copy its `api_id` and `api_hash`.

1. Open Telegram on your phone or desktop and make sure your account is active.

2. Go to Telegram’s developer portal:

   ```text
   https://my.telegram.org
   ```

3. Log in using your Telegram phone number.

4. Telegram will send a confirmation code to your Telegram account.

5. Enter the confirmation code in the website.

6. Click **API development tools**.

7. Create a new application.

8. Fill in the requested fields, such as:

   * App title
   * Short name
   * Platform
   * Description

9. After creating the application, Telegram will show:

   * `api_id`
   * `api_hash`

10. Copy those values into your `.env` file.

Important: keep your `api_hash` private. Do not commit it to GitHub.

## Initial Setup

Clone the repository:

```bash
git clone https://github.com/GaroFOSS/TeleSync.git
cd TeleSync
```

Create a virtual environment.

On Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Copy the example environment file:

On Linux:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
copy .env.example .env
```

Open `.env` and fill in your Telegram credentials:

```env
API_ID=your_api_id_here
API_HASH=your_api_hash_here

SESSION_NAME=folder_uploader
SCAN_INTERVAL_SECONDS=30
APP_STATE_PATH=telesync_state.json
```

Example:

```env
API_ID=12345678
API_HASH=0123456789abcdef0123456789abcdef

SESSION_NAME=folder_uploader
SCAN_INTERVAL_SECONDS=30
APP_STATE_PATH=telesync_state.json
```

## Running the Program

Start the GUI:

```bash
python main.py
```

On the first run, TeleSync will show a Telegram login window.

Login steps:

1. Enter your Telegram phone number in international format.

   Example:

   ```text
   +5511999999999
   ```

2. Click **Request Code**.

3. Check Telegram for the login code.

4. Enter the code in TeleSync.

5. Click **Login**.

6. If your Telegram account has two-step verification enabled, enter your Telegram password when requested.

After the first successful login, TeleSync stores a local Telegram session file. The next time you open the app, it should open directly without asking you to log in again.

## Using the GUI

1. Open TeleSync:

   ```bash
   python main.py
   ```

2. Click **Add Main Folder**.

3. Select the folder you want to sync.

4. Repeat this for every main folder you want to manage.

5. Click **Start Sync**.

For each main folder, TeleSync will:

1. Create a `.telesync/telesync.db` database inside that main folder.
2. Create a Telegram index channel for that main folder.
3. Scan each subfolder.
4. Create a Telegram channel for each subfolder.
5. Send the folder channel invite link to the index channel.
6. Upload new files to the correct folder channel.

## Example

If you add this main folder:

```text
/home/user/Backups
```

And it contains:

```text
/home/user/Backups/Documents
/home/user/Backups/Photos
/home/user/Backups/Projects
```

TeleSync creates:

```text
TeleSync - Backups
Documents
Photos
Projects
```

The `TeleSync - Backups` channel receives links to the `Documents`, `Photos`, and `Projects` channels.

## Database Location

Each main folder has its own database:

```text
<main-folder>/.telesync/telesync.db
```

This database stores:

* The Telegram index channel for the main folder.
* The Telegram upload channel for each subfolder.
* The invite link for each folder channel.
* The files already uploaded.

Because each main folder has its own database, you can move or manage main folders separately.

## Files Ignored by TeleSync

TeleSync ignores:

* Hidden folders and files that start with `.`
* The `.telesync` folder
* Temporary files ending in:

  * `.part`
  * `.tmp`
  * `.crdownload`

## Important Security Notes

Do not commit these files to GitHub:

```text
.env
*.session
*.session-journal
*.db
*.sqlite
*.sqlite3
.telesync/
```

The `.env` file contains your Telegram API credentials.

The `.session` file contains your Telegram login session. Anyone with access to this file may be able to access your Telegram session.

The `.telesync/telesync.db` file may contain Telegram channel IDs, invite links, local file paths, and upload history.

## AI Usage Notice

This project was developed with the assistance of artificial intelligence tools.

AI was used to help design parts of the program structure, customize messages and improve readability.

## License

This project is licensed under the GNU General Public License v3.0 or later.

See the [LICENSE](COPYING) file for details.