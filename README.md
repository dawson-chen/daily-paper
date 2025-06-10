# Daily Paper Bot

This project fetches new papers from arXiv every day using the `arxiv` Python
library, translates the abstract with the DeepSeek large language model
(accessed via the `openai` library), filters them by a specified field and
sends the results to a WeChat group via webhook.

## Requirements

- Python 3.8+
- The Python packages listed in `requirements.txt`.

Install dependencies (internet access required):

```bash
pip install -r requirements.txt
```

## Configuration

Set the following environment variables before running:

- `DEEPSEEK_API_KEY`: API key for the DeepSeek service.
- `DEEPSEEK_API_BASE`: (optional) base URL for the API if different from the
  default OpenAI endpoint.
- `WECHAT_WEBHOOK_KEY`: Key for the WeChat robot webhook.
- `TARGET_FIELD`: (optional) field name used by the classifier.

## Usage

Run the script manually:

```bash
python daily_paper.py
```

The script also schedules itself to run every day at 09:00 server time. You can
keep it running in the background or configure a process manager/cron to start
it automatically.
