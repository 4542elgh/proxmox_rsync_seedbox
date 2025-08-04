import subprocess

class Rsync:
    # rsync -a \
    # --include=/etc --include=/etc/fstab \
    # --include=/home --include=/home/user --include='/home/user/download/***' \
    # --exclude='*' / bkp
    def __init__(self, user:str, seedbox_url:str, sources:list[str], destination:str, port:str, arr_name:str = "", verbose:bool = False) -> None:
        self.user = user
        self.sources = [f"{self.user}@{seedbox_url}:{source}" for source in sources]
        self.destination = destination
        if not port.isdigit():
            raise ValueError("Port must be a valid integer string.")
        self.options = ["--archive", "--compress" , "-e" f"ssh -p {port}"]
        self.verbose = verbose
        print(f"Initialized {arr_name} Rsync transferring sources: {self.sources}")

    def execute(self) -> None:
        # command = ["rsync", *self.options, *self.sources, self.destination]
        command = [
            "rsync",
            *self.options,
            # "ssh -p 34100",
            # "groove1311@direct.seedbox.evanmingliu.com:/home6/groove1311/storage/downloads/qbittorrent/radarr/Birth.of.the.Dragon.2016.1080p.BluRay.REMUX.AVC.DTS-HD.MA.5.1-EPSiLON.mkv",
            # "/Ultrastar/SeedBox/Torrent/radarr"
            *self.sources,
            self.destination
        ]

        if self.verbose:
            print(f"Executing command: {' '.join(command)}")

        # Popen runs the command in background
        subprocess.Popen(command)