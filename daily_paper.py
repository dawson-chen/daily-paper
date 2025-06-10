import os
import time
from datetime import datetime, timedelta

import requests
import schedule
import arxiv
import openai

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_BASE = os.environ.get("DEEPSEEK_API_BASE", "")
WECHAT_WEBHOOK_KEY = os.environ.get("WECHAT_WEBHOOK_KEY", "")
WECHAT_WEBHOOK_URL = (
    "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={key}"
)

FIELD = os.environ.get("TARGET_FIELD", "")

openai.api_key = DEEPSEEK_API_KEY
if DEEPSEEK_API_BASE:
    openai.api_base = DEEPSEEK_API_BASE


def fetch_daily_arxiv_papers(category: str = "cs.LG", max_results: int = 50):
    """Fetch papers submitted in the last day using the arxiv library."""
    yesterday = datetime.utcnow() - timedelta(days=1)
    search = arxiv.Search(
        query=f"cat:{category}",
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )
    papers = []
    for result in search.results():
        if result.published < yesterday:
            break
        authors = [a.name for a in result.authors]
        institutions = [
            getattr(a, "affiliation", "")
            for a in result.authors
            if getattr(a, "affiliation", "")
        ]
        papers.append(
            {
                "title": result.title.strip(),
                "summary": result.summary.strip(),
                "authors": authors,
                "institutions": institutions,
                "link": result.entry_id,
            }
        )
    return papers


def translate_text(text: str) -> str:
    """Translate English text to Chinese using the DeepSeek model."""
    if not DEEPSEEK_API_KEY:
        return text
    try:
        resp = openai.ChatCompletion.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": "Translate the user message from English to Chinese.",
                },
                {"role": "user", "content": text},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        print("Translate failed:", exc)
        return text


def in_target_field(text):
    if not FIELD:
        return True
    if not DEEPSEEK_API_KEY:
        return False
    prompt = f"Does the following abstract belong to the field '{FIELD}'? Answer Yes or No.\n{text}"
    try:
        resp = openai.ChatCompletion.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        answer = resp.choices[0].message.content.strip().lower()
        return answer.startswith("yes")
    except Exception as exc:
        print("Field check failed:", exc)
        return False


def send_wechat_message(content):
    if not WECHAT_WEBHOOK_KEY:
        print("WECHAT_WEBHOOK_KEY not set")
        return
    url = WECHAT_WEBHOOK_URL.format(key=WECHAT_WEBHOOK_KEY)
    payload = {"msgtype": "markdown", "markdown": {"content": content}}
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if not resp.ok:
            print("Failed to send message:", resp.text)
    except requests.RequestException as exc:
        print("Failed to send message:", exc)


def process_papers():
    papers = fetch_daily_arxiv_papers()
    for p in papers:
        if not in_target_field(p["summary"]):
            continue
        translated = translate_text(p["summary"])
        authors = ", ".join(p["authors"])
        institutions = ", ".join(p["institutions"])
        message = (
            f"### {p['title']}\n"
            f"{translated}\n"
            f"**Authors:** {authors}\n"
            f"**Institutions:** {institutions}\n"
            f"[Paper Link]({p['link']})"
        )
        send_wechat_message(message)


def job():
    process_papers()


schedule.every().day.at("09:00").do(job)

if __name__ == "__main__":
    job()
    while True:
        schedule.run_pending()
        time.sleep(60)
