import os
from fastapi import FastAPI
from config.settings import env
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    os.environ["LANGCHAIN_API_KEY"] = env.langsmith_api_key
    os.environ["LANGCHAIN_ENDPOINT"] = env.langsmith_endpoint
    os.environ["LANGCHAIN_TRACING"] = env.langsmith_tracing
    os.environ["LANGCHAIN_PROJECT"] = env.langsmith_project
    print("Langsmith has been set up!")

    yield print("Done")

app = FastAPI(lifespan=lifespan)