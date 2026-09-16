from fastapi import FastAPI

app = FastAPI(title="SupportDesk")


@app.get("/")
def home():
    return {"message": "SupportDesk is running"}