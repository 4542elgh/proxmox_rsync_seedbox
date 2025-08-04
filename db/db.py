from sqlalchemy import create_engine
from db.db_base import Base
from abc import ABC
from db.model.tbl_radarr import RadarrDB
from db.model.tbl_sonarr import SonarrDB

class DB(ABC):
    def __init__(self, verbose: bool = False) -> None:
        # Initialize the database connection and create tables if they do not exist
        self.engine = create_engine('sqlite:///db/database.db', echo=verbose)
        Base.metadata.create_all(self.engine)
    
    def get_engine(self):
        return self.engine