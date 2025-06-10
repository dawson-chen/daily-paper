import os
import time
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
load_dotenv()

import requests
import schedule
import arxiv
import openai
from openai import OpenAI

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_BASE = os.environ.get("DEEPSEEK_API_BASE", "")

FIELD = os.environ.get("TARGET_FIELD", "")

openai.api_key = DEEPSEEK_API_KEY
if DEEPSEEK_API_BASE:
    openai.api_base = DEEPSEEK_API_BASE
    print(f"Using DeepSeek API base: {DEEPSEEK_API_BASE}")


def fetch_daily_arxiv_papers(category: str = "cs.LG", max_results: int = 50):
    """Fetch papers submitted in the last day using the arxiv library."""
    # china_tz = timezone(timedelta(hours=8))
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    start_time = datetime(2025, 6, 9, 0, 0, 0, tzinfo=timezone.utc)
    # Construct the complex query
    query = (
        "cat:cs.* "  # Computer Science category
        "AND ti:agent "  # Title contains "agent"
        "AND abs:reinforcement "  # Abstract contains "reinforcement"
        "AND submittedDate:[202506090000 TO 202506222359]"
    )
    
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )
    results = list(search.results())
    print(f"Found {len(results)} papers")
    papers = []
    for result in results:
        # Convert UTC time to China timezone  .astimezone(china_tz)
        published_time = result.published
        if published_time < start_time:
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
    print(f"Found {len(papers)} papers")
    return papers


def translate_text(text: str) -> str:
    """Translate English text to Chinese using the DeepSeek model."""
    if not DEEPSEEK_API_KEY:
        return text
    try:
        client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_API_BASE)

        resp = client.chat.completions.create(
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
        resp = openai.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        answer = resp.choices[0].message.content.strip().lower()
        return answer.startswith("yes")
    except Exception as exc:
        print("Field check failed:", exc)
        return False



def process_papers():
    papers = fetch_daily_arxiv_papers()
    for p in papers:
        # if not in_target_field(p["summary"]):
        #     continue
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

        print(message)
        print("-" * 100)


def job():
    process_papers()


schedule.every().day.at("09:00").do(job)

if __name__ == "__main__":
    job()
    # while True:
    #     schedule.run_pending()
    #     time.sleep(60)
