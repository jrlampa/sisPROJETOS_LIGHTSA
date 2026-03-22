from fastapi import FastAPI

app = FastAPI(title="sisPROJETOS LIGHT API", version="0.1.0")


@app.get("/")
def hello_world() -> dict[str, str]:
    return {"message": "Hello World - sisPROJETOS LIGHT API"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "api"}
