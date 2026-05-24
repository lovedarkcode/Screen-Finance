from fastapi import FastAPI

app = FastAPI(title="Screen Finance API")


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok", "service": "screen-finance-backend"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}
