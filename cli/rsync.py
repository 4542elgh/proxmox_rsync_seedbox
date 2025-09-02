import os
import psutil
import subprocess
from enum import Enum
from model.torrent import Torrent
from log.log import Log

class ARR(Enum):
    SONARR = "tv-sonarr"
    RADARR = "radarr"

SONARR = ARR.SONARR
RADARR = ARR.RADARR

class Rsync:
    def __init__(self, logger:Log, user:str, seedbox_endpoint:str, sources:list[Torrent], destination:str, port:int, arr_name:ARR) -> None:
        self.logger = logger
        self.user = user
        self.sources = [f"{user}@{seedbox_endpoint}:{source.path}" for source in sources]
        self.destination = destination
        self.port = port
        self.options = ["--archive", "--compress", "--verbose" , "-e" , "ssh -p 34100"]
        self.logger.info("Initialized %s Rsync transferring sources: %s", arr_name.value, sources)

    def execute(self) -> (bool, str):
        if not os.path.exists(self.destination):
            self.logger.error("Destination folder %s does not exist. Please double check path", self.destination)
            exit(1)

        command = [
            "rsync",
            *self.options, # unpack the list into individual strings
            *self.sources,
            self.destination
        ]

        # Run it in frontend if running by Systemd (PID1), running in background with (PID1) will crash rsync
        if psutil.Process(os.getpid()).ppid() == 1:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            _, stderr = process.communicate()

            if process.returncode != 0:
                return (False, stderr)
            else:
                return (True, "")
        # If run by user, just run it in background, so we dont block the cli
        else:
            process = subprocess.Popen(command)
            return (True, "")

def check_running_state() -> bool:
    """
    Check if rsync is currently running.
    """
    try:
        # No process found will return a non-zero exit code
        subprocess.run(['pgrep', 'rsync'], capture_output=True, text=True, check=True)
        # Rsync process found
        return True
    except subprocess.CalledProcessError as _:
        # if e.returncode == 1:
        #     # No rsync process found
        #     return False
        return False
