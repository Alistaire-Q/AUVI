import os
from dotenv import load_dotenv
from arq.connections import RedisSettings

# Load .env file for ARQ worker
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(env_path)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_SSL = str(os.getenv("REDIS_SSL", "false")).lower() == "true"

def get_redis_settings():
    return RedisSettings(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        ssl=REDIS_SSL,
        conn_timeout=15,
        conn_retries=10
    )
