from pydantic_ai.providers.openrouter import OpenRouterProvider
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
import os
from dotenv import load_dotenv
load_dotenv()

ROUTE = os.getenv("ROUTE")
API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")

model = OpenAIModel(ROUTE, provider=OpenRouterProvider(api_key=API_KEY))
agent = Agent(model)
