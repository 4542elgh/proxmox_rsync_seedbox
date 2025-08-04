import os
import paramiko
from enums.enum import DB_ENUM

class SSH:
    def __init__(self, host:str|None, port:str|None, username:str|None) -> None:
        if host is None or port is None or username is None:
            raise ValueError("Host, port, and username must be provided for SSH connection.")
        elif not port.isdigit():
            raise ValueError("Port must be a valid integer string.")
        self.host = host
        self.port = int(port)
        self.username = username
    
    def _list_files(self, path:str|None = None) -> list[str]:
        if path is None:
            print("No path provided, listing home directory.")
            path = '~'
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(self.host, port=self.port, username=self.username)
        
        stdin, stdout, stderr = client.exec_command(f'ls {path}')
        files = stdout.read().decode().splitlines()
        
        client.close()
        return files

    def filter_seedbox_against_api(self, api_queue: set, arr_name: str) -> list[str]:
        """
        Filters the API queue against the files in the specified path on the remote server.
        Returns a list of items that are in both the API queue and the remote directory.
        """
        if arr_name not in [DB_ENUM.SONARR, DB_ENUM.RADARR]:
            raise ValueError(f"Unsupported ARR service: {arr_name}")
        
        if arr_name == DB_ENUM.SONARR:
            seedbox_sonarr = self._list_files(path=os.getenv("SEEDBOX_SONARR_TORRENT_DIR"))
            return [torrent for torrent in api_queue if torrent in seedbox_sonarr]
        else:
            seedbox_radarr = self._list_files(path=os.getenv("SEEDBOX_RADARR_TORRENT_DIR"))
            return [torrent for torrent in api_queue if torrent in seedbox_radarr]