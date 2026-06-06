from pydantic import BaseModel

class TroubleshootRequest(BaseModel):
    error: str
