import os
from dotenv import load_dotenv
from api.Arr import Arr
from ssh.ssh import SSH
from db.db import DB
from db.db_queries import DB_Query
from cli.rsync import Rsync
from cli import rsync
from enums.enum import DB_ENUM, NOTIFICATION_ENUM
from cli.notification import Notification

load_dotenv()

DB_PATH = "db/database.db"

def main(db_verbose:bool=False, verbose:bool=False, dev:bool=False):
    if dev and os.path.exists(DB_PATH):
        os.remove(DB_PATH)  # Remove the database file if it exists, for testing purposes only

    if(rsync.check_running_state()):
        print("Rsync is currently running. Exiting to avoid conflicts.")
        exit(0)

    ArrService = Arr()
    sonarr_api_queue = ArrService.get_api_queue(DB_ENUM.SONARR)
    radarr_api_queue = ArrService.get_api_queue(DB_ENUM.RADARR)

    # # These are imports pending in Arr and exists in seedbox, filtering so only remote seedbox torrent are included
    ssh_conn = SSH(host=os.getenv("SEEDBOX_ENDPOINT"), port=os.getenv("SEEDBOX_PORT"), username=os.getenv("SEEDBOX_USERNAME"))
    sonarr_pending_import = ssh_conn.filter_seedbox_against_api(sonarr_api_queue, DB_ENUM.SONARR)
    radarr_pending_import = ssh_conn.filter_seedbox_against_api(radarr_api_queue, DB_ENUM.RADARR)

    if verbose:
        print("Sonarr list pending import:")
        if len(sonarr_pending_import) == 0:
            print(" - No pending Sonarr imports found.")
        else:
            for item in sonarr_pending_import:
                print(f" - {item}")
        print("Radarr list pending import:")
        if len(radarr_pending_import) == 0:
            print(" - No pending Radarr imports found.")
        else:
            for item in radarr_pending_import:
                print(f" - {item}")

    # # Check against database if the torrent already tried import. Try a max of 3 times before giving up and send Discord message
    db = DB(db_verbose)
    db_engine = db.get_engine()
    db_query = DB_Query(db_engine, query_verbose=verbose)

    # Mark torrent name not in API result list as complete.
    # It either finish transfer or user cancel the import job in Activity Tab
    db_query.mark_db_complete(sonarr_pending_import, DB_ENUM.SONARR)
    db_query.mark_db_complete(radarr_pending_import, DB_ENUM.RADARR)

    # If it does not exists in API anymore, it means the import is complete
    db_query.purge_local_complete_content(os.getenv("SONARR_DEST_DIR"), DB_ENUM.SONARR)
    db_query.purge_local_complete_content(os.getenv("RADARR_DEST_DIR"), DB_ENUM.RADARR)

    # Only return list of full path seedbox torrents not in database (aka. new torrents)
    sonarr_seedbox_torrent_full_path = db_query.check_torrents_and_get_full_path(sonarr_pending_import, DB_ENUM.SONARR)
    radarr_seedbox_torrent_full_path = db_query.check_torrents_and_get_full_path(radarr_pending_import, DB_ENUM.RADARR)

    if len(sonarr_seedbox_torrent_full_path) > 0:
        Rsync(user = os.getenv("SEEDBOX_USERNAME", ""),
            seedbox_url = os.getenv("SEEDBOX_ENDPOINT", ""),
            sources = sonarr_seedbox_torrent_full_path,
            destination = os.getenv("SONARR_DEST_DIR", ""),
            port = os.getenv("SEEDBOX_PORT", "0"),
            arr_name = "Sonarr",
            verbose = verbose).execute()
    elif verbose:
        print("No Sonarr torrents to transfer.")

    if len(radarr_seedbox_torrent_full_path) > 0:
        Rsync(user=os.getenv("SEEDBOX_USERNAME", ""),
            seedbox_url=os.getenv("SEEDBOX_ENDPOINT", ""),
            sources=radarr_seedbox_torrent_full_path,
            destination=os.getenv("RADARR_DEST_DIR", ""),
            port=os.getenv("SEEDBOX_PORT", "0")).execute()
    elif verbose:
        print("No Radarr torrents to transfer.")

    if len(sonarr_seedbox_torrent_full_path) == 0 and len(radarr_seedbox_torrent_full_path) == 0:
        print("No new torrents to transfer.")
    elif len(sonarr_seedbox_torrent_full_path) > 0 or len(radarr_seedbox_torrent_full_path) > 0:
        message = ""

        if len(sonarr_seedbox_torrent_full_path) > 0:
            print(f"Transferred {len(sonarr_seedbox_torrent_full_path)} new Sonarr torrents.")
            message += f"Transferred {len(sonarr_seedbox_torrent_full_path)} new Sonarr torrents:\n"
            message += "\n".join(os.path.basename(path) for path in sonarr_seedbox_torrent_full_path) + "\n"
        if len(radarr_seedbox_torrent_full_path) > 0:
            print(f"Transferred {len(radarr_seedbox_torrent_full_path)} new Radarr torrents.")
            message += f"Transferred {len(sonarr_seedbox_torrent_full_path)} new Radarr torrents:\n"
            message += "\n".join(os.path.basename(path) for path in radarr_seedbox_torrent_full_path) + "\n"

        Notification(os.getenv("WEBHOOK_URL")).send_notification(message)

if __name__ == "__main__":
    main(db_verbose = os.getenv("DB_VERBOSE", "False").lower() == "true",
         verbose = os.getenv("VERBOSE", "False").lower() == "true",
         dev = os.getenv("DEV", "False").lower() == "true")