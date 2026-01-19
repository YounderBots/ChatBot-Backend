from fastapi import APIRouter, HTTPException

from resources.NLPController import router as nlprouter
from resources.TrainController import router as trainingrouter

router = APIRouter()

router.include_router(nlprouter, prefix="/nlp", tags=["NLP"])
router.include_router(trainingrouter, prefix="/nlp", tags=["Train NLP"])
