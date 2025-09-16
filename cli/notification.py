import os
import requests
# from enums.enum import NOTIFICATION_ENUM
from enum import Enum
from log.log import Log

class NOTIFICATION(Enum):
    DISCORD = "discord"
    APPRISE = "apprise"

DISCORD = NOTIFICATION.DISCORD
APPRISE = NOTIFICATION.APPRISE

class Notification:
    """
        Notification is optional, dont need to show in log if not defined
    """
    def __init__(self, logger: Log, webhook_url: str, service: NOTIFICATION) -> None:
        self.logger = logger
        self.WEBHOOK_URL = webhook_url
        self.SERVICE = service
        self.TIMEOUT = 30

    def send_notification(self, message: str, severity: str) -> None:
        if not self.WEBHOOK_URL or not self.SERVICE:
                self.logger.error("Notification service or webhook URL is not set. Skipping notification.")
                return

        payload = {}
        headers = {}
        if self.SERVICE == APPRISE:
            # apprise only support plain text
            payload = {
                "body": message,
                "tags": "all" if os.getenv("APPRISE_TAG") is None else os.getenv("APPRISE_TAG")
            }
            headers = {}

        elif self.SERVICE == DISCORD:
            # Only vanilla Discord Webhook support embeds
            payload = {
                "embeds": [
                    {
                        "title": "Rsync Seedbox",
                        "description": message,
                        "color": 16711680 if severity == "error" else 65280
                    }
                ]
            }
            headers = {
                "Content-Type": "application/json"
            }

        try:
            response = requests.post(
                self.WEBHOOK_URL,
                json = payload,
                headers = headers,
                timeout = self.TIMEOUT)
            response.raise_for_status()
        except requests.RequestException as e:
            self.logger.error(f"Failed to send notification: {e}")
