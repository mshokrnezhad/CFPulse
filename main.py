import os
from utils import get_filename_from_url, download_file, show_diff_and_extract_links

# Set your URL and destination folder here
URL = "https://www.comsoc.org/publications/magazines/ieee-network/cfp"  # <-- Change this to your link
DEST_FOLDER = "downloads"             # <-- Change this to your folder


def main():
    filename = get_filename_from_url(URL)
    new_content, file_path = download_file(URL, DEST_FOLDER, filename)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            old_content = f.read()
        show_diff_and_extract_links(old_content, new_content)
    else:
        print("No previous file found. Saving new file.")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)


if __name__ == "__main__":
    main()
