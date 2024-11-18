import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    POSTGRES_CONN = os.getenv("POSTGRES_CONN")
    HEADLESS = os.getenv('HEADLESS', 'true').lower() in ('true', '1', 't', 'y', 'yes')
    SELECTORS_PATH = os.getenv("SELECTORS_PATH")
