import os
import requests
from api.SonarrResponse import SonarrResponse
from api.RadarrResponse import RadarrResponse
from enum import Enum
from log.log import Log
from model.torrent import Torrent

class enums(Enum):
    SONARR = "tv-sonarr"
    RADARR = "radarr"

SONARR = enums.SONARR
RADARR = enums.RADARR

class Arr():
    def __init__(self, logger: Log):
        self.logger = logger
        self.TIMEOUT = 30

    def _get_queue(self, arr_name, endpoint, api_key) -> SonarrResponse | RadarrResponse | None:
        response = requests.get(
            url = f"{endpoint}/api/v3/queue?pageSize=1000",
            headers = {'X-Api-Key': api_key},
            timeout = self.TIMEOUT)

        if response.status_code == 200:
            try:
                if arr_name == SONARR:
                    return SonarrResponse(**response.json())
                elif arr_name == RADARR:
                    return RadarrResponse(**response.json())
            except requests.JSONDecodeError as e:
                self.logger.error("Error decoding JSON response: %s", e)
                return None
        else:
            raise requests.HTTPError("Failed to fetch Sonarr queue")


    def get_api_queue(self, endpoint:str, api_key:str, arr_name: enums) -> list[Torrent]:
        """
        This gets arr API queue. It will check if queue is torrent then parse outputPath and get path after /radarr /tv-sonarr

        Args:
            arr_name(enums): Arr instance ENUM only

        Returns:
            Set(str): Set of relative path for pending import
        """
        if arr_name not in [SONARR, RADARR]:
            self.logger.warning("Unsupported ARR service: %s", arr_name)

        queue = None
        if arr_name == SONARR and endpoint and api_key:
            queue = self._get_queue(SONARR, endpoint, api_key)
        elif arr_name == RADARR and endpoint and api_key:
            queue = self._get_queue(RADARR, endpoint, api_key)
        else:
            self.logger.warning("Unsupported ARR service: %s endpoint URL or API key not set.", arr_name)
            return []
        self.logger.debug("Service: %s Return records: %s", arr_name.value, queue.records)

        results:list[Torrent] = []
        for record in queue.records:
            if record.protocol == "torrent" and record.trackedDownloadState in ["importPending", "importBlocked"] and record.outputPath is not None:
                output_path = record.outputPath

                # Search for arr term and strip to only relative path, can have many level depth
                index_of = output_path.split("/").index(arr_name.value)
                relative_path = "/".join(output_path.split("/")[index_of + 1:])

                # Emulate a set
                if relative_path not in [res.path for res in results]:
                    # This is only preliminary check, will use "find ./ -type d" to further verify
                    results.append(Torrent(path = relative_path, is_dir = "/" in relative_path))

        self.logger.info("Service: %s Filtered result set: %s", arr_name.value, results)
        return results
