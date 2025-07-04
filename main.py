from utils import *
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
PAGE_ID = os.getenv("NOTION_PAGE_ID")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
TMP_FOLDER = os.getenv("TMP_FOLDER")
KB_FILENAME = os.getenv("KB_FILENAME")
RESULTS_FILENAME = os.getenv("RESULTS_FILENAME")
KB_FILE_PATH = TMP_FOLDER + "/" + KB_FILENAME + ".txt"
RESULTS_FILE_PATH = TMP_FOLDER + "/" + RESULTS_FILENAME + ".json"
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")


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
            text = entry.get('text')
            if href:
                fetch_and_store_linked_file(href, TMP_FOLDER, base, name=name, text=text)
    else:
        print(f"\n--- First time saving: {name} ---")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)


async def main():
    print("\n" + "-" * 50)
    print("STEP 0: Finding New CFPs")
    print("-" * 50)

    # for entry in URLS:
    #     process_url(entry)

    print("\n" + "-" * 50)
    print("STEP 1: Loading KB")
    print("-" * 50)

    # if not PAGE_ID or not NOTION_TOKEN:
    #     print("Please set NOTION_PAGE_ID and NOTION_TOKEN environment variables.")
    # else:
    #     save_notion_markdown(PAGE_ID, NOTION_TOKEN, KB_FILE_PATH)

    print("\n" + "-" * 50)
    print("STEP 2: Loading CFPs")
    print("-" * 50)

    # cfps = load_diff_files(TMP_FOLDER, KB_FILENAME)
    # print(f"Total files processed: {len(cfps)}")

    print("\n" + "-" * 50)
    print("STEP 3: Processing CFPs with AI agent")
    print("-" * 50)

    # for entry in cfps:
    #     if entry['venue'] != 'KB':  # Skip the KB entry itself
    #         kb_entry = next((item for item in cfps if item['venue'] == 'KB'), None)
    #         if kb_entry:
    #             prompt = generate_cfp_prompt(kb_entry['text'], entry['text'])

    #             print(f"\n--- Processing CFP: {entry['title']} ---")
    #             print(f"Venue: {entry['venue']}")
    #             print(f"Link: {entry['link']}")
    #             print("Prompt generated successfully.")
    #             entry['prompt'] = prompt

    #             response = await agent.run(prompt)
    #             # print(response.output)
    #             entry['response'] = response.output

    print("\n" + "-" * 50)
    print("STEP 4: Saving results to JSON file")
    print("-" * 50)

    # save_cfps_to_json(cfps, RESULTS_FILE_PATH)

    print("\n" + "-" * 50)
    print("STEP 5: Emailing results")
    print("-" * 50)

    def create_email_body(filename):
        """
        Creates an email body from the venue, link, and response fields of all entries in cfps.
        Reads cfps data from RESULTS.json file in tmp folder.

        Returns:
            str: Formatted email body
        """
        import json

        # Read cfps from JSON file
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                cfps = json.load(f)
        except FileNotFoundError:
            return "Error: RESULTS.json file not found in tmp folder."
        except json.JSONDecodeError:
            return "Error: Invalid JSON format in RESULTS.json file."

        body = "CFP Analysis Results:\n\n"

        for entry in cfps:
            if entry['venue'] != 'KB':  # Skip the KB entry itself
                body += f"Venue: {entry['venue']}\n"
                body += f"Link: {entry['link']}\n"
                response_text = entry.get('response', 'No response available')
                response_text = response_text.replace('```markdown', '').replace('```', '')
                body += f"\n{response_text}\n"
                body += "-" * 50 + "\n\n"

        return body

    # Create email body from cfps data
    email_body = create_email_body(RESULTS_FILE_PATH)

    send_email_with_attachment(
        subject="CFP Results JSON",
        body=email_body,
        to_email=EMAIL_RECEIVER,
    )
    print("Email sent.")


if __name__ == "__main__":
    asyncio.run(main())
