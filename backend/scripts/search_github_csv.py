import urllib.request
import json
import os

def search_github():
    print("Searching GitHub for fake_job_postings.csv...")
    # List of known repositories that host or fork fake_job_postings.csv
    repo_list = [
        "claireyzy/Fake-Job-Posting-Prediction",
        "davemush/Fake-Job-Postings-Prediction",
        "aditya-s-r/Fake-Job-Posting-Prediction",
        "tanishqvyas/Fake-Job-Posting-Prediction",
        "Nidhi1505/Fake-Job-Posting-Prediction",
        "Siddhesh-Deshmukh/Fake-Job-Posting-Prediction",
        "ashishpatel26/Fake-Job-Posting-Prediction",
        "mushfikur-rahman/Fake-Job-Posting-Prediction",
        "Shivani-2609/Fake-Job-Posting-Prediction",
        "shivambansal/real-or-fake-fake-jobposting-prediction",
        "Mounika129/Fake-Job-Posting-Prediction",
        "saurabh-555/Fake-Job-Prediction",
        "pratyush-24/Fake-Job-Posting-Prediction",
        "Swati2908/Fake-Job-Posting-Prediction",
        "Kusha-99/Fake-Job-Posting-Prediction",
        "sreejit-das/Fake-Job-Posting-Prediction",
        "sourabh-burnwal/Fake-Job-Posting-Prediction",
        "Venkata-Srinivas/Fake-Job-Posting-Prediction",
        "shubham-0209/Fake-Job-Posting-Prediction",
        "mohit-garg/Fake-Job-Posting-Prediction",
        "aniket-sharma/Fake-Job-Posting-Prediction",
        "rohith-kumar/Fake-Job-Posting-Prediction",
        "aishwarya-96/Fake-Job-Posting-Prediction",
        "shristi-21/Fake-Job-Posting-Prediction",
        "yash-sharma-1/Fake-Job-Posting-Prediction",
        "hardik-12/Fake-Job-Posting-Prediction",
        "gautam-123/Fake-Job-Posting-Prediction",
        "harsh-sharma/Fake-Job-Posting-Prediction"
    ]
    
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(data_dir, exist_ok=True)
    target_csv = os.path.join(data_dir, "fake_job_postings.csv")

    for repo in repo_list:
        for branch in ["master", "main"]:
            for path in ["fake_job_postings.csv", "data/fake_job_postings.csv", "Dataset/fake_job_postings.csv", "dataset/fake_job_postings.csv"]:
                url = f"https://raw.githubusercontent.com/{repo}/{branch}/{path}"
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=5) as res:
                        content = res.read()
                        if len(content) > 1000000:
                            print(f"FOUND! {url} ({len(content)} bytes)")
                            with open(target_csv, "wb") as f:
                                f.write(content)
                            return target_csv
                except Exception:
                    pass
    print("None of the hardcoded repos worked.")
    return None

if __name__ == "__main__":
    search_github()
