# CFPulse

A Python application to fetch, process, and analyze Calls for Papers (CFPs) from various IEEE journals, using AI and Notion integration.

## Features
- Downloads and compares CFPs from a list of URLs
- Uses AI to analyze and summarize CFPs
- Sends results via email
- Logs all activity to `cfpulse.log`
- Designed for daily/periodic runs (use cron or scheduler)

## Running with Docker

### 1. Build the Docker Image
```sh
docker build -t cfpulse .
```

### 2. Prepare Your Environment Variables
- Create a `.env` file in your project directory (do **not** commit secrets to git).
- The `.env` file should contain all required environment variables, e.g.:
  ```
  ROUTE=your_route
  API_KEY=your_openai_or_router_api_key
  BASE_URL=your_base_url
  NOTION_PAGE_ID=your_notion_page_id
  NOTION_TOKEN=your_notion_token
  TMP_FOLDER=tmp
  KB_FILENAME=KB
  RESULTS_FILENAME=RESULTS
  EMAIL_RECEIVER=your@email.com
  EMAIL_HOST=smtp.example.com
  EMAIL_PORT=587
  EMAIL_HOST_USER=your@email.com
  EMAIL_HOST_PASSWORD=your_email_password
  ```

### 3. Run the Container
Mount your `.env` file into the container:
```sh
docker run --rm -v $(pwd)/.env:/app/.env cfpulse
```

- The application will log to `cfpulse.log` inside the container. You can mount a volume if you want to persist logs or output files.
- The application will run once and exit. Use a scheduler (like cron or Kubernetes CronJob) to run it periodically.

## Notes
- The image does **not** expose any ports.
- All configuration is via environment variables.
- For production, ensure your `.env` file is kept secure.

## License
MIT 