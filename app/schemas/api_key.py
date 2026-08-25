from pydantic import BaseModel

class ApiKeyResponse(BaseModel):
    api_key:str

