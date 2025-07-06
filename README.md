# CFPulse

<div align="center">
  <img src="cfpulse.png" alt="drawing" width="400"/>
</div>

A Python application that fetches, processes, and analyzes Calls for Papers (CFPs) from various IEEE journals, using AI and Notion integration. Designed for automation and daily reporting.

## Features

- Downloads CFPs from a list of URLs
- Uses AI to analyze and summarize CFPs based on a given set of research intrests
- Sends results via email
- Logs all activity to `cfpulse.log`
- Designed for daily/periodic runs (via Docker and cron)

## Tech Stack

- Python 3.11
- Requests, BeautifulSoup, markdownify, dotenv
- Notion API integration (to get research intrests)
- OpenAI/Router AI integration (via pydantic-ai)
- Email via SMTP
- Docker for containerization

## Setup and Run

### Prerequisites

- Python 3.11 (for local runs) or Docker
- (Optional) Make sure you have `docker` installed for containerized runs
- Prepare your Notion page to connect: [YouTube guide](https://youtu.be/M1gu9MDucMA?si=7DvvA-buMQaj1vg5). We suppose your research intrests are stored in a Notion page.
- Prepare your Gmail to send email with it in Python: [YouTube guide](https://youtu.be/QJobMzcmoMo?si=erZykd9OXITdnJT_). We will email the analysis using Gmail.

### Installation

1. **Clone the repository:**

```bash
git clone https://github.com/yourusername/CFPulse.git
cd CFPulse
```

2. **Create a `.env` file** in the project directory with the following variables:

```bash
ROUTE=your_model_in_openrouter
API_KEY=your_openrouter_api_key
BASE_URL=openrouter_base_url
NOTION_PAGE_ID=your_notion_page_id_including_your_intrests
NOTION_TOKEN=your_notion_token
TMP_FOLDER=tmp
KB_FILENAME=KB
RESULTS_FILENAME=RESULTS
EMAIL_RECEIVER=your@email.com
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=your_email_password
```

3. **Build the Docker image:**

```bash
docker build -t cfpulse .
```

### Running the Application

#### **Manual Run (for testing):**

1. Create the log file if it does not exist:

```bash
touch cfpulse.log
```

2. Run the application in Docker:

```bash
docker run --rm -v $(pwd)/cfpulse.log:/app/cfpulse.log cfpulse
```
- This will run the app once and persist logs to your local `cfpulse.log` file.

#### **Automated Daily Run (using cron):**

To run the app automatically every day at 2:00 AM and persist logs:

1. Open your crontab:
   ```bash
   crontab -e
   ```
2. Add this line:
   ```cron
   0 2 * * * docker run --rm -v $(pwd)/cfpulse.log:/app/cfpulse.log cfpulse
   ```
   - This will run the container daily and append logs to `cfpulse.log` in your project folder.

## How it works

- **Step 1:** Downloads and checks for new CFPs from a list of URLs.
- **Step 2:** Loads your Notion knowledge base as Markdown.
- **Step 3:** Loads and parses all CFP files.
- **Step 4:** Uses an AI agent to analyze and summarize each CFP against your KB.
- **Step 5:** Saves results to a JSON file and sends summary emails.
- **Step 6:** Cleans up temporary files after each run.

---

## Thank You 🙏

Thank you for using CFPulse! This project is designed to automate the tedious process of monitoring and analyzing academic calls for papers. If you have suggestions, issues, or want to contribute, feel free to open an issue or pull request. If you find this project helpful, please star the repo and share your feedback!