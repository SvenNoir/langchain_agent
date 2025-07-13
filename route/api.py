from fastapi import APIRouter
from app.model.AgentModel import input_api
from app.controller.AgentController import AgenticController

router = APIRouter()

@router.post("/query")
async def chatbot(requests: input_api):
    return await AgenticController.graph_call(question = requests)