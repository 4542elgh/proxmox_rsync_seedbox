# type: ignore
import os
import shutil
from datetime import datetime
# from enums.enum import DB_ENUM
import sqlalchemy
from sqlalchemy import select, insert, update, and_
from db.model.tbl_radarr import RadarrDB
from db.model.tbl_sonarr import SonarrDB
from enum import Enum
from log.log import Log
from model.torrent import Torrent

class ARR(Enum):
    SONARR = "tv-sonarr"
    RADARR = "radarr"

SONARR = ARR.SONARR
RADARR = ARR.RADARR

class DB_Query:
    def __init__(self, logger: Log, engine: sqlalchemy.Engine) -> None:
        self.logger = logger
        self.session = engine.connect()

    def mark_db_complete(self, torrents:list[Torrent], arr_name:ARR) -> None:
        """
            Mark database entries not existing in API as completed
            It either:
                1. completed the transfer 
                2. user cancelled it
            It will not mark as complete if:
                1. Title mismatch and require manual intervention
        """
        stmt = None
        if arr_name == SONARR:
            # Done try to change "== False", I tried "is False" and "not var_name", both does not work
            stmt = select(SonarrDB).where(and_(SonarrDB.torrent_name.not_in([torrent.path for torrent in torrents]), SonarrDB.import_complete == False))
        elif arr_name == RADARR:
            stmt = select(RadarrDB).where(and_(RadarrDB.torrent_name.not_in([torrent.path for torrent in torrents]), RadarrDB.import_complete == False))

        result_set = self.session.execute(stmt).all()
        if len(result_set) == 0:
            self.logger.info(f"No entries to mark as complete in {arr_name.value} database.")
            return
        else:
            self.logger.info(f"Found {len(result_set)} entries to mark as complete in {arr_name.value} database.")

        if arr_name == SONARR:
            stmt = update(SonarrDB).where(and_(SonarrDB.torrent_name.not_in([torrent.path for torrent in torrents]), SonarrDB.import_complete == False)).values(dict(import_complete = True, completed_on = datetime.now()))
        else:
            stmt = update(RadarrDB).where(and_(RadarrDB.torrent_name.not_in([torrent.path for torrent in torrents]), RadarrDB.import_complete == False)).values(dict(import_complete = True, completed_on = datetime.now()))

        self.session.execute(stmt)
        self.session.commit()
    
    def purge_local_complete_content(self, arr_dir: str, arr_name: ARR) -> None:
        """ Cleanup local files that finish import process """

        stmt = None
        if arr_name == SONARR:
            stmt = select(SonarrDB).where(and_(SonarrDB.import_complete == True, SonarrDB.purged == False))
        elif arr_name == RADARR:
            stmt = select(RadarrDB).where(and_(RadarrDB.import_complete == True, RadarrDB.purged == False))

        result_set = self.session.execute(stmt).all()
        self.logger.info("Purging %s items from %s local directory.", len(result_set), arr_name.value)

        purge_list = []
        if arr_name == SONARR:
            purge_list = [SonarrDB(*result) for result in result_set]
        elif arr_name == RADARR:
            purge_list = [RadarrDB(*result) for result in result_set]

        for path in [os.path.join(arr_dir, arr.torrent_name) for arr in purge_list]:
            if os.path.exists(path) and not os.path.islink(path):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)

        if arr_name == SONARR:
            stmt = update(SonarrDB).where(SonarrDB.torrent_name.in_([arr.torrent_name for arr in purge_list])).values(purged = True)
        elif arr_name == RADARR:
            stmt = update(RadarrDB).where(RadarrDB.torrent_name.in_([arr.torrent_name for arr in purge_list])).values(purged = True)

        self.session.execute(stmt)
        self.session.commit()
    
    def check_torrents_and_get_full_path(self, torrents: list[Torrent], torrent_path:str, arr_name: ARR) -> list[Torrent]:
        need_transfer:list[Torrent] = []
        for torrent in torrents:
            db_result = None
            if arr_name == SONARR:
                db_result = self._get_torrent(SonarrDB, torrent)
            elif arr_name == RADARR:
                db_result = self._get_torrent(RadarrDB, torrent)

            if db_result is None:
                torrent.notified = False
                need_transfer.append(torrent)
                if arr_name == SONARR:
                    self._add_torrent(SonarrDB, torrent)
                elif arr_name == RADARR:
                    self._add_torrent(RadarrDB, torrent)
            # Pylance lint error
            elif db_result.retries < 3 and not db_result.import_complete:
                need_transfer.append(torrent)
                if arr_name == SONARR:
                    self._increment_retries(SonarrDB, torrent)
                elif arr_name == RADARR:
                    self._increment_retries(RadarrDB, torrent)
            elif db_result.retries == 3 and not db_result.notified and not db_result.import_complete:
                # Send out a dc alert
                self.logger.error("%s's torrent: %s reached 3 retries, please check manually", arr_name.value, os.path.dirname(torrent.path))
            else:
                torrent.notified = db_result.notified
        
        # Return the full path of the seedbox torrents
        for torrent in need_transfer:
            torrent.full_path = os.path.join(torrent_path, torrent.path)
        return need_transfer

    def set_notified(self, arr_name: ARR, torrent: Torrent) -> None:
        database = None
        if arr_name == SONARR:
            database = SonarrDB
        else:
            database = RadarrDB

        stmt = update(database).where(database.torrent_name == torrent.path).values(notified = True)
        self.session.execute(stmt)
        self.session.commit()

    def _add_torrent(self, database, torrent: Torrent) -> None:
        if self._check_exists(database, torrent):
            self.logger.debug("Torrent \"%s\" already exists in the Radarr database.", torrent.path)
            return None
        self._insert(database, torrent)

    def _get_torrent(self, database, torrent: Torrent) -> RadarrDB | SonarrDB | None:
        stmt = select(database).where(database.torrent_name == torrent.path)
        result = self.session.execute(stmt).first()
        if result is None:
            return None
        else:
            # return database(result.id, result.torrent_name)
            return database(**(result._asdict()))

    def _increment_retries(self, database, torrent: Torrent) -> None:
        # Pylance linting error
        stmt = update(database).where(database.torrent_name == torrent.path).values(retries = database.retries + 1)
        self.session.execute(stmt)
        self.session.commit()

    def _check_exists(self, database, torrent: Torrent) -> bool:
        stmt = select(database).where(database.torrent_name == torrent.path).limit(1)
        result_set = self.session.execute(stmt)
        return result_set.first() is not None

    def _insert(self, database, torrent: Torrent) -> None:
        stmt = insert(database).values(torrent_name = torrent.path)
        self.session.execute(stmt)
        self.session.commit()
