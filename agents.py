from pydantic_ai.providers.openrouter import OpenRouterProvider
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Read configuration for AI model
ROUTE = os.getenv("ROUTE")
API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")

# Initialize the OpenAI model with the OpenRouter provider
model = OpenAIModel(ROUTE, provider=OpenRouterProvider(api_key=API_KEY))
# Create an agent instance using the model
agent = Agent(model)
