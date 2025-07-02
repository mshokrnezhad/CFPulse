from utils import get_filename_from_url, download_file, show_diff_and_extract_links
from urls import URLS
import os

DEST_FOLDER = "downloads"


def process_url(entry):
    """
    Process a single URL entry: fetch, compare, and print results.
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
        show_diff_and_extract_links(old_content, new_content, base, element)
    else:
        print(f"\n--- First time saving: {name} ---")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)


def main():
    for entry in URLS:
        process_url(entry)


if __name__ == "__main__":
    main()
