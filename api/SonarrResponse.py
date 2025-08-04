from typing import Optional
from pydantic import BaseModel

class Language(BaseModel):
    id: int
    name: str

class QualityInfo(BaseModel):
    id: int
    name: str
    source: str
    resolution: int

class RevisionInfo(BaseModel):
    version: int
    real: int
    isRepack: bool

class Quality(BaseModel):
    quality: QualityInfo
    revision: RevisionInfo

class StatusMessage(BaseModel):
    title: str
    messages: list[str]

class Record(BaseModel):
    seriesId: int
    episodeId: int
    seasonNumber: int
    languages: list[Language]
    quality: Quality
    customFormats: list[str]
    customFormatScore: int
    size: int
    title: str
    estimatedCompletionTime: str
    added: Optional[str] = None
    status: str
    trackedDownloadStatus: Optional[str] = None
    trackedDownloadState: Optional[str] = None
    statusMessages: Optional[list[StatusMessage]] = None
    errorMessage: Optional[str] = None
    downloadId: Optional[str] = None
    protocol: str
    downloadClient: Optional[str] = None
    downloadClientHasPostImportCategory: bool
    indexer: Optional[str] = None
    outputPath: Optional[str] = None
    episodeHasFile: bool
    sizeleft: int
    timeleft: str
    id: int

class SonarrResponse(BaseModel):
    page: int
    pageSize: int
    sortKey: str
    sortDirection: str
    totalRecords: int
    records: list[Record]
