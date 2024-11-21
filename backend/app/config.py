from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):    
    DATABASE_URL= os.getenv("DATABASE_URL")
    
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    
    YOLO_MODEL_PATH: str = "yolov8n.pt"
    CONFIDENCE_THRESHOLD: float = 0.5
    PROCESS_EVERY_N_FRAMES: int = 3
    
    WS_HEARTBEAT_INTERVAL: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings()
