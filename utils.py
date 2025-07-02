import os
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import difflib
from markdownify import markdownify as md


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
    Shows the unified diff between old and new text, and returns all <a> tag info (href, hreflang, text) from changed lines as a list of dicts.
    Only considers differences inside the specified HTML element if 'element' is provided.
    Args:
        old_text (str): The previous HTML content.
        new_text (str): The new HTML content.
        base (str): The base URL to prepend to hrefs.
        element (str, optional): The HTML tag (with class/id) to scope the diff to.
    Returns:
        list: List of dicts with keys 'href', 'hreflang', 'text' for each <a> tag in changed lines.
    """
    def extract_element_html(html, element):
        if not element:
            return html
        soup = BeautifulSoup(html, 'html.parser')
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
    results = []
    if any(line for line in diff_output if line.startswith('+') and not line.startswith('+++')):
        for line in diff_output:
            if line.startswith('+') and not line.startswith('+++'):
                for href, hreflang, text in extract_href_hreflang_text_from_line(line[1:]):
                    results.append({
                        'href': f"{base}{href}" if href else None,
                        'hreflang': hreflang,
                        'text': text
                    })
        if results:
            print("Found <a> tags in changed parts:")
            for entry in results:
                print("tag: <a>")
                print(f"href: {entry['href']}")
                print(f"text: {entry['text']}")
        else:
            print("No <a> tags with href/hreflang/text found in changed parts.")
    else:
        print("No changes detected.")
    return results


def sanitize_filename(href):
    """
    Create a safe filename from a URL or path, always ending with .txt.
    Args:
        href (str): The href or URL to sanitize.
    Returns:
        str: A safe filename ending with .txt
    """
    parsed = urlparse(href)
    name = os.path.basename(parsed.path)
    if not name:
        name = 'linked_file'
    # Remove query string and fragments
    name = name.split('?')[0].split('#')[0]
    if name.endswith('.html'):
        name = name[:-5]
    name += '.txt'
    return name


def fetch_and_store_linked_file(href, subfolder, base):
    """
    Fetch the content at href, extract <div class="text-long">, convert it to Markdown, and store in subfolder as a .txt file. Use base for relative URLs.
    Args:
        href (str): The href to fetch.
        subfolder (str): The folder to save the file in.
        base (str): The base URL for resolving relative hrefs.
    """
    url = urljoin(base, href)
    filename = sanitize_filename(href)
    file_path = os.path.join(subfolder, filename)
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        div = soup.find('div', class_='text-long')
        if div:
            content = md(str(div))
        else:
            content = '<div class="text-long"> not found'
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fetched and saved <div class='text-long'> as Markdown: {file_path}")
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
