import os
import psutil
import subprocess

class Rsync:
    def __init__(self, user:str, seedbox_url:str, sources:list[str], destination:str, port:str, arr_name:str = "", verbose:bool = False) -> None:
        self.user = user
        self.sources = [f"{self.user}@{seedbox_url}:{source}" for source in sources]
        self.destination = destination
        if not port.isdigit():
            raise ValueError("Port must be a valid integer string.")
        else:
            self.port = port
        self.options = ["--archive", "--compress", "--verbose" , "-e" , "ssh -p 34100" ]
        self.verbose = verbose
        print(f"Initialized {arr_name} Rsync transferring sources: {self.sources}")

    def execute(self) -> (bool, str):
        command = [
            "rsync",
            *self.options,
            *self.sources,
            self.destination
        ]

        if self.verbose:
            print(f"Executing command: {' '.join(command)}")

        # Run it in frontend if running by Systemd (PID1), running in background in Systemd will crash rsync 
        if psutil.Process(os.getpid()).ppid() == 1:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()

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
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            # No rsync process found
            return False
        return False
