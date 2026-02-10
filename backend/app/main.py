from fastapi import FastAPI

app = FastAPI(title="Generador de Horarios API")

@app.get("/")
def read_root():
    return {"message": "Backend operativo 🚀"}