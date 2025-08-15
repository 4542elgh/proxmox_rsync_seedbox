# type: ignore
import os
import shutil
from datetime import datetime
from enums.enum import DB_ENUM
import sqlalchemy
from sqlalchemy import select, insert, update, and_
from db.model.tbl_radarr import RadarrDB
from db.model.tbl_sonarr import SonarrDB

class DB_Query:
    def __init__(self, engine: sqlalchemy.Engine, query_verbose:bool = False) -> None:
        self.session = engine.connect()
        self.query_verbose = query_verbose

    def mark_db_complete(self, torrents:list[str], arr_name:str) -> None:
        """
            Mark database entries not existing in API as completed
            It either:
                1. completed the transfer 
                2. user cancelled it
            It will not mark as complete if:
                1. Title mismatch and require manual intervention
        """
        stmt = None
        if self.query_verbose:
            print(f"Marking {arr_name} DB entries complete since they dont exists in API anymore")
            if arr_name == DB_ENUM.SONARR:
                stmt = select(SonarrDB).where(and_(SonarrDB.torrent_name.not_in(torrents), SonarrDB.import_complete == False))
            elif arr_name == DB_ENUM.RADARR:
                stmt = select(RadarrDB).where(and_(RadarrDB.torrent_name.not_in(torrents), RadarrDB.import_complete == False))
            else:
                print(f"Unknown arr_name: {arr_name}. Must be either Sonarr or Radarr.")
                return

            result_set = self.session.execute(stmt).all()
            if len(result_set) == 0:
                print(f" - No entries to mark as complete in {arr_name} database.")
                return
            else:
                print(f"Found {len(result_set)} entries to mark as complete in {arr_name} database.")
                for result in result_set:
                    print(f" - {result.torrent_name}")

        if arr_name == DB_ENUM.SONARR:
            stmt = update(SonarrDB).where(and_(SonarrDB.torrent_name.not_in(torrents), SonarrDB.import_complete == False)).values(dict(import_complete = True, completed_on = datetime.now()))
        else:
            stmt = update(RadarrDB).where(and_(RadarrDB.torrent_name.not_in(torrents), RadarrDB.import_complete == False)).values(dict(import_complete = True, completed_on = datetime.now()))

        self.session.execute(stmt)
        self.session.commit()
    
    def purge_local_complete_content(self, arr_dir: str | None = None, arr_name: str | None = None) -> None:
        """
            Cleanup local files that finish import process
        """
        if(arr_dir is None or len(arr_dir) == 0 or arr_name is None):
            return

        stmt = None
        if arr_name == DB_ENUM.SONARR:
            stmt = select(SonarrDB).where(and_(SonarrDB.import_complete == True, SonarrDB.purged == False))
        elif arr_name == DB_ENUM.RADARR:
            stmt = select(RadarrDB).where(and_(RadarrDB.import_complete == True, RadarrDB.purged == False))
        else:
            print(f"Unknown arr_name: {arr_name}. Must be either Sonarr or Radarr.")
            return

        result_set = self.session.execute(stmt).all()
        if self.query_verbose:
            print(f"Purging {arr_name}'s local complete content.")
            if len(result_set) == 0:
                print(f" - No {arr_name} entries to purge.")
                return None
            else:
                print(f"Found {len(result_set)} {arr_name} entries to purge.")
                for result in result_set:
                    print(f" - {result.torrent_name}")

        purge_list = []
        if arr_name == DB_ENUM.SONARR:
            purge_list = [SonarrDB(*result) for result in result_set]
        else:
            purge_list = [RadarrDB(*result) for result in result_set]

        purge_full_path = [os.path.join(arr_dir, arr.torrent_name) for arr in purge_list]
        
        if self.query_verbose:
            print(f"Purging {len(purge_full_path)} entries from local storage.")
            for path in purge_full_path:
                print(f" - {path}")

        for path in purge_full_path:
            if os.path.exists(path) and not os.path.islink(path):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            else:
                print(f"Path {path} does not exist or is a symlink, skipping deletion.")

        purge_names = [arr.torrent_name for arr in purge_list]
        if self.query_verbose:
            print(f"Flag {len(purge_names)} entries from {arr_name} database. purged = True")
            for name in purge_names:
                print(f" - {name}")

        if arr_name == DB_ENUM.SONARR:
            stmt = update(SonarrDB).where(SonarrDB.torrent_name.in_(purge_names)).values(purged = True)
        else:
            stmt = update(RadarrDB).where(RadarrDB.torrent_name.in_(purge_names)).values(purged = True)

        self.session.execute(stmt)
        self.session.commit()
    
    def check_torrents_and_get_full_path(self, torrents: list[str], arr_name: str) -> list[str]:
        need_transfer = []
        for torrent in torrents:
            db_result = None
            if arr_name == DB_ENUM.SONARR:
                db_result = self._get_torrent(SonarrDB, torrent)
            elif arr_name == DB_ENUM.RADARR:
                db_result = self._get_torrent(RadarrDB, torrent)

            if db_result is None:
                if arr_name == DB_ENUM.SONARR:
                    self._add_torrent(SonarrDB, torrent)
                elif arr_name == DB_ENUM.RADARR:
                    self._add_torrent(RadarrDB, torrent)
                need_transfer.append(torrent)
            # Pylance lint error
            elif db_result.retries < 3 and not db_result.import_complete:
                if arr_name == DB_ENUM.SONARR:
                    self._increment_retries(SonarrDB, torrent)
                elif arr_name == DB_ENUM.RADARR:
                    self._increment_retries(RadarrDB, torrent)
                need_transfer.append(torrent)
            elif db_result.retries == 3 and not db_result.notified:
                # Send out a dc alert
                print(f"{arr_name}'s torrent: {torrent} reached 3 retries, please check manually")
        
        # Return the full path of the seedbox torrents
        if arr_name == DB_ENUM.SONARR:
            return [os.path.join(os.getenv("SEEDBOX_SONARR_TORRENT_DIR", ""), item) for item in need_transfer]
        elif arr_name == DB_ENUM.RADARR:
            return [os.path.join(os.getenv("SEEDBOX_RADARR_TORRENT_DIR", ""), item) for item in need_transfer]

    def _add_torrent(self, database, torrent_name:str|None=None) -> None:
        if not torrent_name:
            return None
        if self._check_exists(database, torrent_name):
            print(f"Torrent \"{torrent_name}\" already exists in the Radarr database.")
            return None
        self._insert(database, torrent_name)
        print(f"Added torrent: \"{torrent_name}\" to the Radarr database.")

    def _get_torrent(self, database, torrent_name: str | None = None) -> RadarrDB | SonarrDB | None:
        if torrent_name is None:
            return None
        # Pylance linting error
        stmt = select(database).where(database.torrent_name == torrent_name)
        result = self.session.execute(stmt).first()
        if result is None:
            return None
        else:
            return database(result.torrent_name)

    def _increment_retries(self, database, torrent_name: str) -> None:
        if torrent_name is None:
            return None
        # Pylance linting error
        stmt = update(database).where(database.torrent_name == torrent_name).values(retries = database.retries + 1)
        self.session.execute(stmt)
        self.session.commit()

    def _check_exists(self, database, torrent_name: str) -> bool:
        stmt = select(database).where(database.torrent_name == torrent_name).limit(1)
        result_set = self.session.execute(stmt)
        return result_set.first() is not None

    def _insert(self, database, torrent_name: str) -> None:
        stmt = insert(database).values(torrent_name=torrent_name)
        self.session.execute(stmt)
        self.session.commit()
