import subprocess

def check_rsync_running_state() -> bool:
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