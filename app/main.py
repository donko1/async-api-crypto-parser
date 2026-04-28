from re import L

from config.settings import SettingsManager
from fastapi import FastAPI

from services.MarketDataService import MarketDataService
from core.logger import get_logger

app = FastAPI(
    title="Crypto parser API", version="0.0.1", docs_url="/docs", redoc_url="/redoc"
)

parser_service = MarketDataService()

logger = get_logger("fastapi main.py")


@app.get("/")
async def root():
    return {"Message": "Crypto parser API", "status": "active"}


@app.get("/start_parser")
async def start_parser():
    await parser_service.start_parsing()
    return {"Message": "Crypto parser started", "status": "active"}


@app.get("/stop_parser")
async def stop_parser():
    await parser_service.stop_parsing()
    return {"Message": "Crypto parser stopped", "status": "inactive"}


@app.get("/status")
async def status_parser():
    return parser_service.get_status()


@app.post("/change_settings_value")
async def change_setting_value(key, new_value):
    settings = SettingsManager()
    try:
        settings.set(key, new_value)
        return {"Message": f"Setting '{key}' updated to '{new_value}'"}
    except ValueError as e:
        logger.error(f"Error updating setting: {e}")
        return {"Key does not exist"}
