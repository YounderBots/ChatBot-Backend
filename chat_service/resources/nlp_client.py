import time

import httpx

NLP_URL = "http://localhost:8001/nlp/parse"
MAX_RETRIES = 3


async def analyze_text(text: str) -> dict:
    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                res = await client.post(NLP_URL, json={"text": text})
                res.raise_for_status()
                return res.json()
        except Exception:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(0.5)
