from fastapi import APIRouter
from app.schemas.task import Occurrence

router = APIRouter()


@router.get("/", response_model=list[Occurrence])
async def list_occurrences():
    # TODO: récupérer les occurrences depuis la base de données
    return []
