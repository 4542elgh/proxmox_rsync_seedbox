from pydantic import BaseModel
from typing import Optional

# I have not test all possible fields, so some fields might not exists and require Optional[Type] to avoid validation error

class Language(BaseModel):
    id: int
    name: str

class QualityInfo(BaseModel):
    id: int
    name: str
    source: str
    resolution: int
    modifier: str

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
    movieId: int
    languages: list[Language]
    quality: Quality
    customFormats: list[str]
    customFormatScore: int
    size: int
    title: str
    estimatedCompletionTime: str
    added: str
    status: str
    trackedDownloadStatus: Optional[str] = None
    trackedDownloadState: Optional[str] = None
    statusMessages: Optional[list[StatusMessage]] = None
    errorMessage: Optional[str] = None
    downloadId: Optional[str] = None
    protocol: str
    downloadClient: Optional[str] = None
    downloadClientHasPostImportCategory: bool
    indexer: str
    outputPath: Optional[str] = None
    sizeleft: int
    timeleft: str
    id: int

class RadarrResponse(BaseModel):
    page: int
    pageSize: int
    sortKey: str
    sortDirection: str
    totalRecords: int
    records: list[Record]