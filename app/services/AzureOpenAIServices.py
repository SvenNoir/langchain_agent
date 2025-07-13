
from config.settings import env
from langchain_openai import AzureChatOpenAI


def AzureService():
    llm = AzureChatOpenAI(
        azure_endpoint = env.azure_openai_endpoint, 
        azure_deployment = env.azure_openai_deployment,
        openai_api_version = env.azure_openai_api_version,
        api_key = env.azure_openai_api_key,
        temperature = 0,
        max_retries = 3,
    )
    return llm