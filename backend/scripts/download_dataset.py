import os
import urllib.request
import re

def download_emsad_dataset():
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(data_dir, exist_ok=True)
    target_csv = os.path.join(data_dir, "fake_job_postings.csv")

    if os.path.exists(target_csv) and os.path.getsize(target_csv) > 1000000:
        print(f"Dataset already exists at {target_csv} ({os.path.getsize(target_csv)} bytes)")
        return target_csv

    # Candidate URLs for EMSAD fake_job_postings.csv
    candidates = [
        "https://raw.githubusercontent.com/saurabh-555/Fake-Job-Prediction/master/fake_job_postings.csv",
        "https://raw.githubusercontent.com/Shivamb/real-or-fake-fake-jobposting-prediction/master/fake_job_postings.csv",
        "https://raw.githubusercontent.com/Rounak-Sharma/Fake-Job-Postings-Prediction/master/fake_job_postings.csv",
        "https://raw.githubusercontent.com/hoangsonww/Spot-the-Scam-AI-Job-Fraud/main/fake_job_postings.csv",
        "https://raw.githubusercontent.com/dair-ai/emotion/main/fake_job_postings.csv",
        "https://raw.githubusercontent.com/38832/Fake-Job-Posting-Prediction/master/fake_job_postings.csv"
    ]

    # Try searching duckduckgo html for raw github link
    try:
        ddg_url = "https://html.duckduckgo.com/html/?q=site:raw.githubusercontent.com+fake_job_postings.csv"
        req = urllib.request.Request(ddg_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8', errors='ignore')
        discovered = re.findall(r'https://raw\.githubusercontent\.com/[^\s"\'<>]+fake_job_postings\.csv', html)
        for d in discovered:
            if d not in candidates:
                candidates.insert(0, d)
    except Exception as e:
        print("DuckDuckGo discovery skipped:", e)

    print(f"Testing {len(candidates)} candidate URLs...")
    for url in candidates:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as res:
                content = res.read()
                if len(content) > 1000000:  # EMSAD is ~12-15 MB
                    with open(target_csv, "wb") as f:
                        f.write(content)
                    print(f"Successfully downloaded EMSAD dataset from {url} ({len(content)} bytes)")
                    return target_csv
        except Exception as err:
            print(f"Failed {url}: {err}")

    raise RuntimeError("Could not download EMSAD dataset from any candidate URL.")

if __name__ == "__main__":
    download_emsad_dataset()
