class Torrent():
    def __init__(self, path: str, is_dir: bool):
        self._path = path
        self._is_dir = is_dir

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, path:str):
        self._path = path

    @property
    def is_dir(self):
        return self._is_dir

    @is_dir.setter
    def is_dir(self, is_dir:bool):
        self._is_dir = is_dir
