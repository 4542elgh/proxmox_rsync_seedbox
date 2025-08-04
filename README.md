# rsync synchronization script
This project is aimed to reduce `rsync` cloning entire remote seedbox content to local for Radarr/Sonarr to import. (A major waste of disk space). This script will look at Radarr/Sonarr's queue and grab matching file/directory from seedbox to local drive so Radarr/Sonarr can import them. Then the file/directory will be deleted to save space. Such file/directory name will mark as synced in a `sqlite3` database to keep track and never `rsync` the same file/directory again.

**This script will only grab (only work with) what is requested from your local Sonarr/Radarr instance.**

# Features
- **Selective Sync**: Only transfers files that are pending import in local Radarr/Sonarr instance.
- **Seedbox Filtering**: Ensures files exist on the remote seedbox before attempting transfer.
- **Database Tracking**: Uses SQLite to track import attempts, retries, and completion status.
- **Automatic Cleanup**: Deletes files locally after successful import and marks them as purged in the database.
- **Retry Logic**: Retries failed imports up to 3 times before requiring manual intervention.
    - **TODO: Trigger notification system via apprise or discord webhook**
- **API Integration**: Fetches queue data from Radarr/Sonarr via their APIs.
- **SSH & Rsync**: Uses SSH for remote file listing and rsync for file transfer.
- **Environment Configuration**: All credentials and paths are managed via `.env`

# Setup
## 1. Install pip dependencies
```bash
    pip install -r requirements.txt
```
## 2. Environment Variables
Create a `.env` file from `.env.example` in the project root. Replace all keys with your own Arr credentials. Debugging messages are off by default

## 3. Run application
Source the `.venv` directory (please do use a virtual environment, just for good practice) and run the `main.py` script:
```bash
    python main.py
```

4. How It Works
API Queue Fetch: Gets the list of torrents pending import from Radarr/Sonarr.
Seedbox Filtering: Checks which of these files exist on the seedbox via SSH.
Database Check: Determines which files are new or need to be retried (up to 3 times).
Rsync Transfer: Transfers eligible files from the seedbox to the local import directory.
Mark Complete: Marks files not in the API queue as completed in the database.
Purge: Deletes local files that have been successfully imported and marks them as purged.
Key Modules
main.py: Entry point, orchestrates the workflow.
Arr.py: Handles API requests to Radarr/Sonarr.
ssh.py: SSH connection and remote file listing.
rsync.py: Rsync wrapper for file transfer.
db.py, db_queries.py: Database setup and queries.
tbl_radarr.py, tbl_sonarr.py: Database models.
Database Schema
tbl_radarr / tbl_sonarr
id: Primary key
torrent_name: Name of the torrent
retries: Number of import attempts
import_complete: Boolean, import status
notified: Boolean, notification sent after max retries
purged: Boolean, file deleted locally
completed_on: DateTime, when marked complete
API Models
See RadarrResponse.py and SonarrResponse.py for full response models.

Troubleshooting
Ensure all environment variables are set correctly.
Check SSH connectivity to the seedbox.
Make sure rsync is installed and accessible.
Review verbose logs for errors.
License
This project is for personal use. See .gitignore for excluded files and folders.

For more details, see the source code and comments in each module.