from utils import get_filename_from_url, download_file, show_diff_and_extract_links, fetch_and_store_linked_file, save_notion_markdown
from urls import URLS
import os
from agents import agent
from pydantic_ai.providers.openrouter import OpenRouterProvider
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from dotenv import load_dotenv
import asyncio

DEST_FOLDER = "downloads"

load_dotenv()

ROUTE = os.getenv("ROUTE")
API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")
page_id = os.getenv("NOTION_PAGE_ID")
notion_token = os.getenv("NOTION_TOKEN")

model = OpenAIModel(ROUTE, provider=OpenRouterProvider(api_key=API_KEY))
agent = Agent(model)


def process_url(entry):
    """
    Process a single URL entry: fetch, compare, print results, and fetch linked <a> hrefs.
    Args:
        entry (dict): Contains 'name', 'base', 'url', and 'element'.
    """
    name = entry['name']
    url = entry['url']
    base = entry['base']
    element = entry.get('element')
    subfolder = os.path.join(DEST_FOLDER, name)
    filename = get_filename_from_url(url)
    new_content, file_path = download_file(url, subfolder, filename)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            old_content = f.read()
        print(f"\n--- Checking: {name} ---")
        results = show_diff_and_extract_links(old_content, new_content, base, element)
        for entry in results:
            href = entry['href']
            if href:
                fetch_and_store_linked_file(href, subfolder, base)
    else:
        print(f"\n--- First time saving: {name} ---")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)


async def main():
    # for entry in URLS:
    #     process_url(entry)

    # Save Notion page as KB if env vars are set
    if not page_id or not notion_token:
        print("Please set NOTION_PAGE_ID and NOTION_TOKEN environment variables.")
    else:
        save_notion_markdown(page_id, notion_token)

    # response = await agent.run("What is the capital of France?")
    # print(response.output)


if __name__ == "__main__":
    asyncio.run(main())
