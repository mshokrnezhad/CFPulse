import os
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import difflib


def get_filename_from_url(url):
    """
    Extracts a filename from the given URL. If the URL does not contain a filename, returns 'downloaded_file.html'.
    Ensures the filename ends with .html.
    Args:
        url (str): The URL to extract the filename from.
    Returns:
        str: The extracted or default filename.
    """
    local_filename = os.path.basename(urlparse(url).path)
    if not local_filename:
        local_filename = 'downloaded_file.html'
    if not local_filename.endswith('.html'):
        local_filename += '.html'
    return local_filename


def download_file(url, dest_folder, filename):
    """
    Downloads the content from the given URL and saves it in the specified folder with the given filename.
    Creates the folder if it does not exist.
    Args:
        url (str): The URL to download from.
        dest_folder (str): The folder to save the file in.
        filename (str): The name of the file to save.
    Returns:
        tuple: (content as str, full file path as str)
    """
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
    file_path = os.path.join(dest_folder, filename)
    response = requests.get(url)
    response.raise_for_status()
    return response.text, file_path


def extract_href_hreflang_text_from_line(line):
    """
    Parses a line of HTML and extracts all <a> tags, returning their href, hreflang, and text content.
    Args:
        line (str): The HTML line to parse.
    Returns:
        list of tuples: Each tuple contains (href, hreflang, text) for an <a> tag.
    """
    soup = BeautifulSoup(line, 'html.parser')
    results = []
    for a in soup.find_all('a'):
        href = a.get('href')
        hreflang = a.get('hreflang')
        text = a.get_text(strip=True)
        results.append((href, hreflang, text))
    return results


def show_diff_and_extract_links(old_text, new_text, base, element=None):
    """
    Shows the unified diff between old and new text, and prints href and text from <a> tags in changed lines.
    Only considers differences inside the specified HTML element if 'element' is provided.
    Args:
        old_text (str): The previous HTML content.
        new_text (str): The new HTML content.
        base (str): The base URL to prepend to hrefs.
        element (str, optional): The HTML tag (with class/id) to scope the diff to.
    Returns:
        bool: True if differences were found, False otherwise.
    """
    def extract_element_html(html, element):
        if not element:
            return html
        soup = BeautifulSoup(html, 'html.parser')
        # Try to parse element as a tag with class or id
        import re
        tag_match = re.match(r'<(\w+)([^>]*)>', element)
        if not tag_match:
            return html
        tag = tag_match.group(1)
        attrs_str = tag_match.group(2)
        attrs = {}
        class_match = re.search(r'class=["\']([^"\']+)["\']', attrs_str)
        if class_match:
            attrs['class'] = class_match.group(1).split()
        id_match = re.search(r'id=["\']([^"\']+)["\']', attrs_str)
        if id_match:
            attrs['id'] = id_match.group(1)
        el = soup.find(tag, attrs=attrs)
        return str(el) if el else ''

    if element:
        old_text = extract_element_html(old_text, element)
        new_text = extract_element_html(new_text, element)

    old_lines = old_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)
    diff = difflib.unified_diff(old_lines, new_lines, fromfile='old', tofile='new')
    diff_output = list(diff)
    if any(line for line in diff_output if line.startswith('+') and not line.startswith('+++')):
        links = []
        for line in diff_output:
            if line.startswith('+') and not line.startswith('+++'):
                links.extend(extract_href_hreflang_text_from_line(line[1:]))
        if links:
            for href, _, text in links:
                print(f"href: {base}{href}, \ntext: {text}")
        else:
            print("No <a> tags with href/hreflang/text found in changed parts.")
        return True
    else:
        print("No changes detected.")
        return False
