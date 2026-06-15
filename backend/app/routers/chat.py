from fastapi import APIRouter
from app.schemas.chat import ChatRequest
from app.services.chat_orchestrator import route_message

router = APIRouter()


@router.post("/api/chat")
def chat(req: ChatRequest):
    result = route_message(req.message)
    return result
