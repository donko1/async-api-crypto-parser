from fastapi import FastAPI

app = FastAPI(
    title="Crypto parser API", version="0.0.1", docs_url="/docs", redoc_url="/redoc"
)


@app.get("/")
async def root():
    return {"Message": "Crypto parser API", "status": "active"}
