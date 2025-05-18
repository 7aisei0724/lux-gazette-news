import os
import datetime
import requests
import pdfplumber
import openai
import markdown

# OpenAI APIキーを環境変数から読み込み
openai.api_key = os.getenv("OPENAI_API_KEY")

# 官報PDFのURL（dateは YYYY-MM-DD 形式）
BASE_URL = "https://legilux.public.lu/eli/etat/leg/{date}.pdf"

def download_pdf(date: str, path: str):
    url = BASE_URL.format(date=date)
    r = requests.get(url, timeout=30)
    r.raise_for_status()  # エラー時例外発生
    with open(path, "wb") as f:
        f.write(r.content)

def extract_text(path: str) -> str:
    with pdfplumber.open(path) as pdf:
        # 全ページのテキスト抽出し結合
        return "\n".join(page.extract_text() or "" for page in pdf.pages)

def summarize(text: str) -> str:
    prompt = f"""
You are a professional legal/finance journalist.
Summarize the following Luxembourg Official Gazette
in concise English bullet points (max 200 words),
emphasising changes relevant to business, finance, and law.

TEXT:
{text[:12000]}  # トークン節約のため最大12000文字にカット
"""
    res = openai.ChatCompletion.create(
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
    # フォルダがなければ作成（site/src/content）
    os.makedirs("site/src/content", exist_ok=True)
    with open(f"site/src/content/{date}.md", "w") as f:
        f.write(md)

if __name__ == "__main__":
    today = datetime.date.today().strftime("%Y-%m-%d")
    pdf_path = f"gazette_{today}.pdf"

    print("Downloading PDF...")
    download_pdf(today, pdf_path)

    print("Extracting text...")
    text = extract_text(pdf_path)

    print("Summarizing...")
    summary = summarize(text)

    print("Saving markdown...")
    save_markdown(summary, today)

    print("✅ Article generated:", today)
