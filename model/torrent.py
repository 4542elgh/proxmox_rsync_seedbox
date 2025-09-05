class Torrent():
    def __init__(self, path: str, is_dir: bool, notified:bool = False):
        self._path = path
        self._full_path = None
        self._is_dir = is_dir
        self._notified = notified

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, path:str):
        self._path = path

    @property
    def full_path(self):
        return self._full_path

    @full_path.setter
    def full_path(self, full_path:str):
        self._full_path = full_path

    @property
    def is_dir(self):
        return self._is_dir

    @is_dir.setter
    def is_dir(self, is_dir:bool):
        self._is_dir = is_dir

    @property
    def notified(self):
        return self._notified

    @notified.setter
    def notified(self, notified:bool):
        self._notified = notified
