from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL : str
    ALGORITHM  : str
    JWT_EXPIRE_MINUTES  : int
    SECRET_KEY  : str
    REDIS_URL : str

    class Config:
        env_file = ".env"


settings = Settings()

