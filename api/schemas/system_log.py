from datetime import datetime

from pydantic import BaseModel


class SystemLog(BaseModel):
    id: int
    timestamp: datetime
    level: str
    source: str
    message: str

    class Config:
        from_attributes = True
