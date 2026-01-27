import os
import subprocess

import httpx
import yaml
from configs.base_config import BaseConfig
from fastapi import APIRouter, HTTPException

router = APIRouter()
RASA_DATA_PATH = "./rasa/data/nlu.yml"


@router.post("/train")
async def train():

    async with httpx.AsyncClient(timeout=10) as client:
        res = await client.get(f"{BaseConfig.ADMIN_EXPORT_URL}/nlp/export")
        res.raise_for_status()
        training_data = res.json()
        print(training_data)

    if not training_data.get("intents"):
        raise HTTPException(400, "No training data found")

    nlu_payload = {"version": "3.1", "nlu": []}

    for intent in training_data["intents"]:
        examples = "\n".join(f"- {p}" for p in intent["phrases"])
        nlu_payload["nlu"].append({"intent": intent["name"], "examples": examples})

    os.makedirs(os.path.dirname(RASA_DATA_PATH), exist_ok=True)

    with open(RASA_DATA_PATH, "w", encoding="utf-8") as f:
        yaml.dump(nlu_payload, f, sort_keys=False)

    process = subprocess.run(
        ["rasa", "train", "nlu"], capture_output=True, text=True, check=True
    )

    if process.returncode != 0:
        raise HTTPException(status_code=500, detail=process.stderr)

    return {"status": "success", "message": "RASA model trained successfully"}
