import os
import sys
import datetime
import requests
import pdfplumber
from openai import OpenAI
import markdown
from dotenv import load_dotenv

load_dotenv()  # .env を読み込む
client = OpenAI()


# 官報PDFのURL（dateは YYYY-MM-DD 形式）
BASE_URL = "https://legilux.public.lu/eli/etat/leg/{date}.pdf"

def download_pdf(date: str, path: str) -> bool:
    url = BASE_URL.format(date=date)
    try:
        r = requests.get(url, timeout=30)
        if r.status_code != 200 or r.headers.get("Content-Type") != "application/pdf":
            print(f"⚠️ PDFが見つかりませんでした: {url}")
            return False
        with open(path, "wb") as f:
            f.write(r.content)
        return True
    except Exception as e:
        print(f"❌ ダウンロードエラー: {e}")
        return False

def extract_text(path: str) -> str:
    with pdfplumber.open(path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)

def summarize(text: str) -> str:
    prompt = f"""
You are a professional legal/finance journalist.
Summarize the following Luxembourg Official Gazette
in concise English bullet points (max 200 words),
emphasising changes relevant to business, finance, and law.

TEXT:
{text[:12000]}
"""
    res = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return res.choices[0].message.content.strip()

def save_markdown(summary: str, date: str):
    md = f"""---
title: Luxembourg Official Gazette – {date}
pubDate: {date}
description: AI-generated English summary of the Luxembourg Government Gazette dated {date}
---

{summary}
"""
    os.makedirs("site/src/content", exist_ok=True)
    with open(f"site/src/content/{date}.md", "w") as f:
        f.write(md)

if __name__ == "__main__":
    # 日付の取得
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        date_str = datetime.date.today().strftime("%Y-%m-%d")

    pdf_path = f"gazette_{date_str}.pdf"

    if not os.path.exists(pdf_path):
        print(f"📥 Downloading PDF for {date_str}...")
        if not download_pdf(date_str, pdf_path):
            print("⏭ スキップしました（PDF未発行）")
            exit(0)
    else:
        print(f"📄 Using local PDF file: {pdf_path}")

    print("📄 Extracting text...")
    text = extract_text(pdf_path)

    print("🧠 Summarizing with GPT...")
    summary = summarize(text)

    print("📝 Saving markdown...")
    save_markdown(summary, date_str)

    print("✅ Article generated:", date_str)
