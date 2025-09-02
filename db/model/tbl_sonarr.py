from sqlalchemy import Column, Date, Integer, String, Boolean, DateTime
from db.db_base import Base

class SonarrDB(Base):
    __tablename__ = "tbl_sonarr"

    id = Column(Integer, primary_key=True)
    torrent_name = Column(String, nullable=False)
    retries = Column(Integer, nullable=False, default=1)
    import_complete = Column(Boolean, nullable=False, default=False)
    notified = Column(Boolean, nullable=False, default=False)
    completed_on = Column(DateTime, nullable=True)
    purged = Column(Boolean, nullable=False, default=False)
    is_dir = Column(Boolean, nullable=False, default=False)

    def __init__(self, id:int, torrent_name: str, retries: int = 1, import_complete: bool = False, notified: bool = False, completed_on: str | None = None, purged: bool = False, is_dir: bool = False):
        self.id = id
        self.torrent_name = torrent_name
        self.retries = retries
        self.import_complete = import_complete
        self.notified = notified
        self.completed_on = completed_on
        self.purged = purged
        self.is_dir = is_dir
