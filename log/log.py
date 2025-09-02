import logging

class Log:
    def __init__(self, level:str) -> None:
        logging.basicConfig(
            format='%(asctime)s %(levelname)-8s %(message)s',
            encoding="utf-8",
            # filemode="a",
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.FileHandler("app.log"),
                logging.StreamHandler()
            ]
        )
        # logging.getLogger().addHandler(logging.StreamHandler())

        if level == "debug":
            logging.getLogger().setLevel(level=logging.DEBUG)
        elif level == "info":
            logging.getLogger().setLevel(level=logging.INFO)
        else:
            logging.getLogger().setLevel(level=logging.ERROR)
        
        self.logger = logging.getLogger(__name__)
    
    # Argument forwarding
    def debug(self, *args, **kwargs) -> None:
        self.logger.debug(*args, **kwargs)

    def info(self, *args, **kwargs) -> None:
        self.logger.info(*args, **kwargs)

    def warning(self, *args, **kwargs) -> None:
        self.logger.warning(*args, **kwargs)

    def error(self, *args, **kwargs) -> None:
        self.logger.error(*args, **kwargs)