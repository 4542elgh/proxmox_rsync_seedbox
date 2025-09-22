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
    def __init__(self, logger:Log) -> None:
        self.logger = logger

    def transfer_from_remote(self, user:str, seedbox_endpoint:str, sources:list[Torrent], destination:str, port:int, arr_name:ARR) -> (bool, str):
        sources_full_path = [f"{user}@{seedbox_endpoint}:{source.full_path}" for source in sources]
        options = ["--archive",
                    "--no-compress", # --compress might be killing performance, in face we specifically use no-compress
                    "--whole-file",
                    "--sparse",
                    "--acls",
                    "--xattrs",
                    "--executability",
                    "--verbose" ,
                    "-e" ,
                    "ssh -p " + str(port)]
        self.logger.info("Initialized %s Rsync transferring sources: %s", arr_name.value, sources)

        if not os.path.exists(destination):
            self.logger.error("Destination folder %s does not exist. Please double check path", destination)
            exit(1)

        command = [
            "rsync",
            *options, # unpack the list into individual strings
            *sources_full_path,
            destination
        ]

        # Run in foreground (blocking) if running by Systemd (PID1), running in background with (PID1) will crash rsync
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
