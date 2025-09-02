import os
from dotenv import load_dotenv

load_dotenv()

# Sonarr
SONARR_ENDPOINT:str = os.getenv("SONARR_ENDPOINT", "")
SONARR_API_KEY:str = os.getenv("SONARR_API_KEY", "")
SONARR_DEST_DIR:str = os.getenv("SONARR_DEST_DIR", "")

# Radarr
RADARR_ENDPOINT:str = os.getenv("RADARR_ENDPOINT", "")
RADARR_API_KEY:str = os.getenv("RADARR_API_KEY", "")
RADARR_DEST_DIR:str = os.getenv("RADARR_DEST_DIR", "")

# Seedbox
SEEDBOX_USERNAME:str = os.getenv("SEEDBOX_USERNAME", "")
SEEDBOX_ENDPOINT:str = os.getenv("SEEDBOX_ENDPOINT", "")
SEEDBOX_PORT:int = int(os.getenv("SEEDBOX_PORT", "")) if os.getenv("SEEDBOX_PORT", "").isdigit() else 0

SEEDBOX_SONARR_TORRENT_PATH:str = os.getenv("SEEDBOX_SONARR_TORRENT_PATH", "")
SEEDBOX_RADARR_TORRENT_PATH:str = os.getenv("SEEDBOX_RADARR_TORRENT_PATH", "")

# Notification
NOTIFICATION_SERVICE:str = os.getenv("NOTIFICATION_SERVICE", "") # Options: "apprise", "discord"
WEBHOOK_URL:str = os.getenv("WEBHOOK_URL", "") # Omit this line to disable notifications
APPRISE_TAG:str = os.getenv("APPRISE_TAG", "") # Only for apprise notifications

DEV:bool = os.getenv("DEV", "").lower() in ["true", "1", "t"] # Set to True to remove and recreate the database for testing purposes
VERBOSE:str = os.getenv("VERBOSE", "").lower() if os.getenv("VERBOSE", "").lower() in ["debug", "info", "error"] else "error" # Default to error log level
DB_VERBOSE:bool = os.getenv("DB_VERBOSE", "").lower() in ["true", "1", "t"] # Set to True to enable database operation logging
DB_PATH:str = os.getenv("db/database.db", "")
