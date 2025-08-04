from sqlalchemy import Column, Date, Integer, String, Boolean, DateTime
from db.db_base import Base

class SonarrDB(Base):
    __tablename__ = "tbl_sonarr"

    id = Column(Integer, primary_key=True)
    torrent_name = Column(String, nullable=False)
    retries = Column(Integer, nullable=False, default=1)
    import_complete = Column(Boolean, nullable=False, default=False)
    notified = Column(Boolean, nullable=False, default=False)
    purged = Column(Boolean, nullable=False, default=False)
    completed_on = Column(DateTime, nullable=True)

    def __init__(self, id: int, torrent_name: str, retries: int, import_complete: bool, notified: bool = False, completed_on: str | None = None, purged: bool = False):
        self.id = id
        self.torrent_name = torrent_name
        self.retries = retries
        self.import_complete = import_complete
        self.notified = notified
        self.completed_on = completed_on
        self.purged = purged
