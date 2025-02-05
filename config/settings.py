from pydantic_settings import BaseSettings
from pydantic import BaseModel
from dotenv import load_dotenv
import os


load_dotenv()


DB_URL: str = os.environ.get("DB_URL")

CORS_ORIGIN: str = os.environ.get("CORS_ORIGIN")

TEST_DB_URL: str = os.environ.get("TEST_DB_URL")

PORT: int = os.environ.get("PORT")


class RunConfig(BaseModel):
    port: int = PORT



class CORSConfig(BaseModel):
    origin: str = CORS_ORIGIN



class DBConfig(BaseModel):
    url: str = DB_URL
    echo: bool = True
    echo_pool: bool = True
    pool_size: int = 10
    test_url: str = TEST_DB_URL



#----------------------------------------------------------------
class Settings(BaseSettings):
    db: DBConfig = DBConfig()
    cors: CORSConfig = CORSConfig()
    run: RunConfig = RunConfig()
    

settings = Settings()