from re import L

from fastapi import FastAPI

from services.MarketDataService import MarketDataService

app = FastAPI(
    title="Crypto parser API", version="0.0.1", docs_url="/docs", redoc_url="/redoc"
)

parser_service = MarketDataService()


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


# @app.post()
# async def change_env_value():
