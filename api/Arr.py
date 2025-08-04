import os
import requests
from api.SonarrResponse import SonarrResponse
from api.RadarrResponse import RadarrResponse
from enums.enum import DB_ENUM

class Arr:
    def __init__(self):
        self.SONARR_ENDPOINT = os.getenv("SONARR_ENDPOINT")
        self.SONARR_API_KEY = os.getenv("SONARR_API_KEY")
        self.RADARR_ENDPOINT = os.getenv("RADARR_ENDPOINT")
        self.RADARR_API_KEY = os.getenv("RADARR_API_KEY")

    def _get_sonarr_queue(self) -> SonarrResponse | None:
        if self.SONARR_API_KEY:
            headers = {'X-Api-Key': self.SONARR_API_KEY}
            response = requests.get(f"{self.SONARR_ENDPOINT}/api/v3/queue?pageSize=1000", headers=headers, timeout=30)
            if response.status_code == 200:
                try:
                    return SonarrResponse(**response.json())
                except requests.JSONDecodeError as e:
                    print(f"Error decoding JSON response: {e}")
                    return None
            else:
                raise requests.HTTPError("Failed to fetch Sonarr queue")
        else:
            print("API key is required for Sonarr API access")
            exit(1)

    def _get_radarr_queue(self) -> RadarrResponse | None:
        if self.RADARR_API_KEY:
            headers = {'X-Api-Key': self.RADARR_API_KEY}
            response = requests.get(f"{self.RADARR_ENDPOINT}/api/v3/queue?pageSize=1000", headers=headers, timeout=30)
            if response.status_code == 200:
                try:
                    return RadarrResponse(**response.json())
                except requests.JSONDecodeError as e:
                    print(f"Error decoding JSON response: {e}")
                    return None
            else:
                raise requests.HTTPError("Failed to fetch Sonarr queue")
        else:
            print("API key is required for Sonarr API access")
            exit(1)

    def get_api_queue(self, arr_name: str) -> set[str]:
        queue = None
        if arr_name == DB_ENUM.SONARR and self.SONARR_API_KEY:
            queue = self._get_sonarr_queue()
        elif arr_name == DB_ENUM.RADARR and self.RADARR_API_KEY:
            queue = self._get_radarr_queue()
        else:
            print(f"Unsupported ARR service: {arr_name} or API key not set.")
            return set()
        return set([record.title for record in queue.records if record.protocol == "torrent" and record.trackedDownloadState == "importPending"])