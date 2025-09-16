import os
from api import Arr
from ssh import ssh
from db import db, db_queries
from cli import rsync, notification, permission
import config
from log.log import Log
from model.torrent import Torrent
import shutil


def main(logger:Log) -> None:
    # Get a copy of production db
    if config.DEV:
        if os.path.exists(config.DB_PATH):
            os.remove(config.DB_PATH)  # Remove the database file if it exists, for testing purposes only
        shutil.copy2("/usr/local/bin/proxmox_rsync_seedbox/db/database.db", f"{config.DB_PATH}")

    if(rsync.check_running_state()):
        logger.error("Rsync is currently running. Exiting to avoid conflicts.")
        exit(0)

    arr_service = Arr.Arr(logger = logger)

    # These queue should represent the torrents file name, not display name (they can be different such that file name might delimit by . but display name delimit by space)
    sonarr_api_queue:list[Torrent] = arr_service.get_api_queue(config.SONARR_ENDPOINT, config.SONARR_API_KEY, Arr.SONARR)
    radarr_api_queue:list[Torrent] = arr_service.get_api_queue(config.RADARR_ENDPOINT, config.RADARR_API_KEY, Arr.RADARR)
    
    ssh_conn = ssh.SSH(logger = logger,
                    host = config.SEEDBOX_ENDPOINT,
                    port = config.SEEDBOX_PORT,
                    username = config.SEEDBOX_USERNAME)

    # # These are imports pending in Arr and exists in seedbox, filtering so only remote seedbox torrent are included
    sonarr_pending_import = ssh_conn.filter_seedbox_against_api(config.SEEDBOX_SONARR_TORRENT_PATH, sonarr_api_queue, ssh.SONARR)
    logger.info("Sonarr pending import exists in Seedbox: %s", sonarr_pending_import)
    radarr_pending_import = ssh_conn.filter_seedbox_against_api(config.SEEDBOX_RADARR_TORRENT_PATH, radarr_api_queue, ssh.RADARR)
    logger.info("Radarr pending import exists in Seedbox: %s", radarr_pending_import)

    # # Check against database if the torrent already tried import. Try a max of 3 times before giving up and send Discord message
    db_engine = db.DB(logger)
    db_engine = db_engine.get_engine()
    db_query = db_queries.DB_Query(logger, db_engine)

    # Mark torrent name not in API result list as complete.
    # It either finish transfer or user cancel the import job in Activity Tab
    db_query.mark_db_complete(sonarr_pending_import, db_queries.SONARR)
    db_query.mark_db_complete(radarr_pending_import, db_queries.RADARR)

    # If it does not exists in API anymore, it means the import is complete
    db_query.purge_local_complete_content(config.SONARR_DEST_DIR, db_queries.SONARR)
    db_query.purge_local_complete_content(config.RADARR_DEST_DIR, db_queries.RADARR)

    # Only return list of full path seedbox torrents not in database (aka. new torrents)
    sonarr_seedbox_torrent:list[Torrent] = db_query.check_torrents_and_get_full_path(sonarr_pending_import, config.SEEDBOX_SONARR_TORRENT_PATH, db_queries.SONARR)
    radarr_seedbox_torrent:list[Torrent] = db_query.check_torrents_and_get_full_path(radarr_pending_import, config.SEEDBOX_RADARR_TORRENT_PATH, db_queries.RADARR)

    perm = permission.Permission()
    perm.update_permission(config.SONARR_DEST_DIR, sonarr_seedbox_torrent, config.CHOWN_UID, config.CHOWN_GID, config.CHMOD)
    perm.update_permission(config.RADARR_DEST_DIR, radarr_seedbox_torrent, config.CHOWN_UID, config.CHOWN_GID, config.CHMOD)

    rsync_util = rsync.Rsync(logger)

    sonarr_rsync_status = False
    sonarr_rsync_msg = ""
    if len(sonarr_seedbox_torrent) > 0:
        sonarr_rsync_status, sonarr_rsync_msg = rsync_util.transfer_from_remote(
            user = config.SEEDBOX_USERNAME,
            seedbox_endpoint = config.SEEDBOX_ENDPOINT,
            port = config.SEEDBOX_PORT,
            sources = sonarr_seedbox_torrent,
            destination = config.SONARR_DEST_DIR,
            arr_name = rsync.SONARR)
    else:
        logger.info("No Sonarr torrents to transfer.")

    radarr_rsync_status = False
    radarr_rsync_msg = ""
    if len(radarr_seedbox_torrent) > 0:
        radarr_rsync_status, radarr_rsync_msg = rsync_util.transfer_from_remote(
            user = config.SEEDBOX_USERNAME,
            seedbox_endpoint = config.SEEDBOX_ENDPOINT,
            port = config.SEEDBOX_PORT,
            sources = radarr_seedbox_torrent,
            destination = config.RADARR_DEST_DIR,
            arr_name=rsync.RADARR)
    else:
        logger.info("No Radarr torrents to transfer.")

    perm = permission.Permission()
    perm.update_permission(config.SONARR_DEST_DIR, sonarr_seedbox_torrent, config.CHOWN_UID, config.CHOWN_GID, config.CHMOD)
    perm.update_permission(config.RADARR_DEST_DIR, radarr_seedbox_torrent, config.CHOWN_UID, config.CHOWN_GID, config.CHMOD)

    # Only notify ones that has not been notified. Dont want to spam Discord
    sonarr_need_notify = [torrent for torrent in sonarr_seedbox_torrent if not torrent.notified]
    radarr_need_notify = [torrent for torrent in radarr_seedbox_torrent if not torrent.notified]

    if len(sonarr_need_notify) == 0 and len(radarr_need_notify) == 0:
        logger.info("No new torrents to transfer.")
    elif len(sonarr_need_notify) > 0 or len(radarr_need_notify) > 0:
        message = ""
        severity = "message"

        if len(sonarr_need_notify) > 0:
            if sonarr_rsync_status:
                logger.info(f"Transferred {len(sonarr_need_notify)} new Sonarr torrents.")
                message += f"Transferred {len(sonarr_need_notify)} new Sonarr torrents:\n"
                message += "\n".join(os.path.basename(torrent.path) for torrent in sonarr_need_notify) + "\n"
            else:
                logger.error(f"Transferred failed for Sonarr torrents with error message: {sonarr_rsync_msg}")
                message += f"Transferred faild for Sonarr torrents with error message: {sonarr_rsync_msg}"
                severity = "error"
            for torrent in sonarr_need_notify:
                db_query.set_notified(db_queries.SONARR, torrent)

        if len(radarr_need_notify) > 0:
            if radarr_rsync_status:
                logger.info(f"Transferred {len(radarr_need_notify)} new Radarr torrents.")
                message += f"Transferred {len(radarr_need_notify)} new Radarr torrents:\n"
                message += "\n".join(os.path.basename(torrent.path) for torrent in radarr_need_notify) + "\n"
            else:
                logger.error(f"Transferred faild for Radarr torrents with error message: {radarr_rsync_msg}")
                message += f"Transferred faild for Radarr torrents with error message: {radarr_rsync_msg}"
                severity = "error"
            for torrent in radarr_need_notify:
                db_query.set_notified(db_queries.RADARR, torrent)

        if config.NOTIFICATION_SERVICE and config.NOTIFICATION_SERVICE.lower() == "apprise":
            notification.Notification(logger, config.WEBHOOK_URL, notification.APPRISE).send_notification(message, severity)
        elif config.NOTIFICATION_SERVICE and config.NOTIFICATION_SERVICE.lower() == "discord":
            notification.Notification(logger, config.WEBHOOK_URL, notification.DISCORD).send_notification(message, severity)

if __name__ == "__main__":
    main(Log(config.VERBOSE))
