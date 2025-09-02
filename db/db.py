from sqlalchemy import create_engine
from db.db_base import Base
from abc import ABC
from db.model.tbl_radarr import RadarrDB
from db.model.tbl_sonarr import SonarrDB
from log.log import Log

class DB(ABC):

    def __init__(self, logger: Log) -> None:
        self.logger = logger
        # Initialize the database connection and create tables if they do not exist
        self.engine = create_engine('sqlite:///db/database.db')
        Base.metadata.create_all(self.engine)
    
    def get_engine(self):
        return self.engine


