import paramiko
from enum import Enum
from log.log import Log
from model.torrent import Torrent

class ARR(Enum):
    SONARR = "tv-sonarr"
    RADARR = "radarr"

SONARR = ARR.SONARR
RADARR = ARR.RADARR

class FILETYPE(Enum):
    DIR = "Dir"
    FILE = "File"

DIR = FILETYPE.DIR
FILE = FILETYPE.FILE

class SSH:
    def __init__(self, logger:Log, host:str, port:int, username:str) -> None:
        self.logger = logger

        if host is None or username is None or port is None:
            self.logger.error("Host, port, and username must be provided for SSH connection.")

        self.host:str = host
        self.username:str = username
        self.port:int = port
    
    def _list(self, path:str, filetype: FILETYPE, arr_type: ARR) -> list[str]:
        options = ["-type d"] if filetype == DIR else ["-type f"]
        options.append("-maxdepth 1")

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(self.host, port=self.port, username=self.username)

        cmd = f'find {path} {" ".join(options)}'
        self.logger.debug("Executing remote command: %s", cmd)
        _, stdout, stderr = client.exec_command(cmd)

        if len(stderr.readlines()) != 0:
            self.logger.error("Error from Paramiko: %s", stderr.readlines())
            return []
        else:
            listing = stdout.read().decode().splitlines()
            
            client.close()
            # Only get relative path, and remove prepending /
            listing = [item.strip().split(arr_type.value)[1][1:] for item in listing]
            # find ./ -type d -maxdepth 1 have first entry of dir itself, remove relative path of ""
            # find ./ -type f -maxdepth 1 does not have this issue
            return [item for item in listing if item.strip() != ""]

    def filter_seedbox_against_api(self, arr_path:str, api_queue: list[Torrent], arr_name: ARR) -> list[Torrent]:
        """
        Filters the API queue against the files in the specified path on the remote server.
        Returns a list of items that are in both the API queue and the remote directory.
        """
        if arr_name not in [SONARR, RADARR]:
            self.logger.error("Unsupported ARR service: %s", arr_name)
            return []

        result = api_queue.copy()

        # Getting seedbox dir and files
        seedbox_arr_dir = self._list(arr_path, DIR, arr_name)
        seedbox_arr_file = self._list(arr_path, FILE, arr_name)

        self.logger.debug("Seedbox %s dir: %s", arr_name.value, seedbox_arr_dir)
        self.logger.debug("Seedbox %s file: %s", arr_name.value, seedbox_arr_file)
        self.logger.debug("local sonarr: %s", api_queue)

        # Fine tune is_dir parameter
        for torrent in result:
            potential_path = torrent.path.split("/")[0]
            if potential_path in seedbox_arr_dir:
                torrent.is_dir = True
                torrent.path = potential_path
            elif potential_path in seedbox_arr_file:
                torrent.is_dir = False
            self.logger.debug("Cannot find %s in remote %s file nor dir")
        
        return result
