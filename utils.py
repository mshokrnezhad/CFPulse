import os
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import difflib
from markdownify import markdownify as md
import re
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import logging

load_dotenv()

EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = os.getenv("EMAIL_PORT")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")

logging.basicConfig(
    filename='cfpulse.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


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
            logging.info("Found <a> tags in changed parts:")
            for entry in results:
                logging.info("tag: <a>")
                logging.info(f"href: {entry['href']}")
                logging.info(f"text: {entry['text']}")
        else:
            logging.info("No <a> tags with href/hreflang/text found in changed parts.")
    else:
        logging.info("No changes detected.")
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


def fetch_and_store_linked_file(href, subfolder, base, name=None, text=None):
    """
    Fetch the content at href, extract <div class="text-long">, convert it to Markdown, and store in subfolder as a .txt file. Use base for relative URLs.
    Args:
        href (str): The href to fetch.
        subfolder (str): The folder to save the file in.
        base (str): The base URL for resolving relative hrefs.
        name (str, optional): The name of the entry (journal/source).
        text (str, optional): The anchor text of the link.
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
            f.write(f"Venue: {name}\n" if name else "")
            f.write(f"Link: {href}\n")
            f.write(f"Title: {text}\n" if text else "")
            f.write("-----\n\n")
            f.write(content)
        logging.info(f"Fetched and saved a new CFP for {name} as Markdown: {file_path}")
    except Exception as e:
        logging.error(f"Failed to fetch {url}: {e}")


def fetch_notion_blocks(page_id, notion_token):
    logging.info(f"Fetching blocks for page/block: {page_id}")
    url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Notion-Version": "2022-06-28"
    }
    blocks = []
    next_cursor = None
    while True:
        params = {}
        if next_cursor:
            params['start_cursor'] = next_cursor
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        blocks.extend(data.get('results', []))
        logging.info(f"Fetched {len(data.get('results', []))} blocks (total so far: {len(blocks)})")
        if data.get('has_more'):
            next_cursor = data['next_cursor']
        else:
            break
    return blocks


def block_to_markdown(block, notion_token):
    block_type = block['type']
    logging.info(f"Processing block type: {block_type}")
    md = ""
    if block_type == 'paragraph':
        text = ''.join([t['plain_text'] for t in block['paragraph']['rich_text']])
        md += text + '\n\n'
    elif block_type == 'heading_1':
        text = ''.join([t['plain_text'] for t in block['heading_1']['rich_text']])
        md += f"# {text}\n\n"
    elif block_type == 'heading_2':
        text = ''.join([t['plain_text'] for t in block['heading_2']['rich_text']])
        md += f"## {text}\n\n"
    elif block_type == 'heading_3':
        text = ''.join([t['plain_text'] for t in block['heading_3']['rich_text']])
        md += f"### {text}\n\n"
    elif block_type == 'bulleted_list_item':
        text = ''.join([t['plain_text'] for t in block['bulleted_list_item']['rich_text']])
        md += f"- {text}\n"
    elif block_type == 'numbered_list_item':
        text = ''.join([t['plain_text'] for t in block['numbered_list_item']['rich_text']])
        md += f"1. {text}\n"
    # Add more block types as needed...

    # Recursively process children if they exist
    if block.get('has_children'):
        logging.info(f"Block {block['id']} has children, fetching recursively...")
        child_blocks = fetch_notion_blocks(block['id'], notion_token)
        for child in child_blocks:
            md += block_to_markdown(child, notion_token)
    return md


def notion_page_to_markdown(page_id, notion_token):
    logging.info(f"Converting Notion page {page_id} to Markdown...")
    blocks = fetch_notion_blocks(page_id, notion_token)
    md = ""
    for block in blocks:
        md += block_to_markdown(block, notion_token)
    logging.info(f"Finished converting Notion page {page_id} to Markdown.")
    return md


def save_notion_markdown(page_id, notion_token, filename):
    logging.info(f"Saving Notion page {page_id} as Markdown to {filename}...")
    md = notion_page_to_markdown(page_id, notion_token)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(md)
    logging.info(f"Saved Notion page as Markdown to {filename}")


def load_diff_files(folder, kb_filename):
    """
    Read all files in the tmp folder and extract venue, link, title, and text.
    Returns a list of dictionaries with the specified attributes.
    """
    files_data = []

    if not os.path.exists(folder):
        logging.error(f"TMP_FOLDER {folder} does not exist.")
        return files_data

    for filename in os.listdir(folder):
        if filename.endswith('.txt'):
            file_path = os.path.join(folder, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()

                if filename == kb_filename + ".txt":
                    # For KB file, set venue, link, title to "KB"
                    file_data = {
                        'venue': 'KB',
                        'link': 'KB',
                        'title': 'KB',
                        'text': content
                    }
                else:
                    # For other files, extract from first three lines
                    lines = content.split('\n')
                    venue = lines[0] if len(lines) > 0 else ''
                    link = lines[1] if len(lines) > 1 else ''
                    title = lines[2] if len(lines) > 2 else ''

                    # Remove the first three lines from text content
                    text_lines = lines[3:] if len(lines) > 3 else []
                    text = '\n'.join(text_lines).strip()

                    file_data = {
                        'venue': venue,
                        'link': link,
                        'title': title,
                        'text': text
                    }

                files_data.append(file_data)
                logging.info(f"Processed file: {filename}")

            except Exception as e:
                logging.error(f"Error reading file {filename}: {e}")

    return files_data


def generate_cfp_prompt(kb_text, cfp_text):
    """
    Generate a prompt comparing a CFP to KB research interests.

    Args:
        kb_text (str): The knowledge base text containing research interests
        cfp_text (str): The call for papers text

    Returns:
        str: The formatted prompt for comparison
    """
    return f"""Suppose that <KB> is my research interests, and <CFP> is a new call for paper.
        Compare <CFP> with <KB> by applying the rules specified in <RULES>, and return the results in <STRUCTURE> format.
        
        <RULES>
        - If at least one of the directions listed in <CFP> is also mentioned in <KB>, then <CFP> is a 4/4 fit with <KB>.
        - If none of the directions match, but there is a match in all three of the following categories—use cases, objectives, and constraints (i.e., at least one match in each)—then <CFP> is a 3/4 fit with <KB>.
        - If none of the directions match, but there is a match in any two of the following categories—use cases, objectives, and constraints (i.e., at least one match in two categories)—then <CFP> is a 2/4 fit with <KB>.
        - If none of the directions match, but there is a match in at least one of the categories—use cases, objectives, or constraints—then <CFP> is a 1/4 fit with <KB>.
        - If there are no matches in directions, use cases, objectives, or constraints, then <CFP> is a 0/4 fit with <KB>.
        </RULES>

        <STRUCTURE>
        <br><br><b>Key Overlaps and Fits:</b><br><br>
        write plain, unformatted text that estimates the fit score (0/4, 1/4, 2/4, 3/4, 4/4) and explains any point in <CFP> which can be directly addressed by <KB>, based on the fit determined using the rules defined in <RULES>. avoid itemization.
        <br><br><b>Potential Gaps or Misalignments:</b><br><br>
        write plain, unformatted text that explains any point in <CFP> that could be used to extend or enhance <KB>. Specify which parts of <KB> each point could be applied to. avoid itemization.
        <br><br><b>Suggested Submission Angles</b><br><br>
        write plain, unformatted text that summarizes fits and gaps and directs the reader to the following suggested papers for possible submission based on <CFP> and <KB>. avoid itemization.
        <br><br><b>Title 1: write paper title here</b><br>
        <b>Abstract:</b> write paper abstract here
        <br><br><b>Title 2: write paper title here</b><br>
        <b>Abstract:</b> write paper abstract here
        <br><br><b>Title 3: write paper title here</b><br>
        <b>Abstract:</b> write paper abstract here<br>
        <br><br>write a message to the reader encouraging him to check the link to the CFP for more details. do not include any link here.<br>
        </STRUCTURE>
        
        RETURN A RESPONSE JUST INCLUDING THE ABOVE <STRUCTURE> IN HTML FORMAT. DONT ADD/RETURN ANYTHING ELSE.
        
        <KB>
        {kb_text}
        </KB>

        <CFP>
        {cfp_text}
        </CFP>
    """


def save_cfps_to_json(cfps, filename):
    """
    Save the processed CFPs data to a JSON file.

    Args:
        cfps (list): List of dictionaries containing CFP data
        filename (str): The filename to save the JSON to
    """
    import json

    # Create the full file path
    file_path = os.path.join(filename)

    # Convert the data to JSON-serializable format
    json_data = []
    for entry in cfps:
        json_entry = {
            'venue': entry['venue'],
            'link': entry['link'],
            'title': entry['title'],
            'text': entry['text'],
            'prompt': entry.get('prompt', ''),
            'response': entry.get('response', '')
        }
        json_data.append(json_entry)

    # Write to JSON file
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        logging.info(f"CFPs data saved to {file_path}")
    except Exception as e:
        logging.error(f"Error saving CFPs to JSON: {e}")


def send_email_with_attachment(subject, body, to_email):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_HOST_USER
    msg["To"] = to_email
    # Set plain text fallback
    msg.set_content("This email requires an HTML-compatible email client.")
    # Add HTML version
    msg.add_alternative(body, subtype='html')

    # # Attach the file (if needed in the future)
    # with open(attachment_path, "rb") as f:
    #     file_data = f.read()
    #     file_name = os.path.basename(attachment_path)
    # msg.add_attachment(file_data, maintype="application", subtype="octet-stream", filename=file_name)

    # Send the email
    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
        server.starttls()
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        server.send_message(msg)


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
            response_text = response_text.replace('```html', '').replace('```', '')
            body += f"\n{response_text}\n"
            # body += "-" * 50 + "\n\n"

    return body


def create_email_body_for_entry(entry):
    """
    Creates an email body from the venue, link, and response fields of an entry.

    Returns:
        str: Formatted email body
    """

    body = ""

    body += f"{entry['link']}\n"
    response_text = entry.get('response', 'No response available')
    response_text = response_text.replace('```markdown', '').replace('```', '')
    body += f"\n{response_text}\n"
    # body += "-" * 50 + "\n\n"

    return body


def send_failure_alert(subject, message, to_email):
    from email.message import EmailMessage
    import smtplib
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_HOST_USER
    msg["To"] = to_email
    msg.set_content(message)
    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
        server.starttls()
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        server.send_message(msg)


def cleanup_tmp_folder(tmp_folder):
    try:
        for filename in os.listdir(tmp_folder):
            file_path = os.path.join(tmp_folder, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
                logging.info(f"Removed file: {filename}")
        logging.info(f"Successfully cleaned temporary folder: {tmp_folder}")
    except Exception as e:
        logging.error(f"Error cleaning temporary folder: {e}")
