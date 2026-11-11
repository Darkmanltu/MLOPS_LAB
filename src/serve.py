import os
from contextlib import asynccontextmanager
import mlflow, mlflow.sklearn
from fastapi import FastAPI, HTTPException
from mlflow import MlflowClient
from pydantic import BaseModel

MODEL_NAME = os.getenv("MODEL_NAME", "agnews-clf")
ALIAS = os.getenv("MODEL_ALIAS", "champion")
state = {}


@asynccontextmanager
async def lifespan(app):
    # servisas randa modelį pagal alias'ą registre, o ne iš failo
    mv = MlflowClient().get_model_version_by_alias(MODEL_NAME, ALIAS)
    state["version"] = mv.version
    state["model"] = mlflow.sklearn.load_model(f"models:/{MODEL_NAME}@{ALIAS}")
    yield


app = FastAPI(lifespan=lifespan)


class Req(BaseModel):
    texts: list[str]


@app.get("/health")
def health():
    if "model" not in state:
        raise HTTPException(503, "model not loaded")
    return {"status": "ok", "model": MODEL_NAME, "version": state["version"]}


@app.post("/predict")
def predict(req: Req):
    return {"labels": [int(x) for x in state["model"].predict(req.texts)],
            "version": state["version"]}