import urllib.request
import csv
import json

candidate_urls = [
    "https://raw.githubusercontent.com/shivamb/real-or-fake-fake-jobposting-prediction/master/fake_job_postings.csv",
    "https://raw.githubusercontent.com/sardend/Real-or-Fake-Job-Posting-Prediction/master/fake_job_postings.csv",
    "https://raw.githubusercontent.com/aditya-kushwaha/Fake-Job-Posting-Prediction/master/fake_job_postings.csv",
    "https://raw.githubusercontent.com/subhadiptamajumdar/Fake-Job-Posting-Prediction/master/fake_job_postings.csv",
    "https://raw.githubusercontent.com/amankharwal/Website-Data/master/fake_job_postings.csv",
    "https://raw.githubusercontent.com/shubh-garg/fake-job-postings/main/fake_job_postings.csv",
    "https://raw.githubusercontent.com/sardend/Fake-Job-Posting-Prediction/main/fake_job_postings.csv",
    "https://raw.githubusercontent.com/laxmimerit/All-CSV-ML-Files/master/fake_job_postings.csv",
    "https://raw.githubusercontent.com/AashishSaini/Fake-Job-Posting-Prediction/master/fake_job_postings.csv",
    "https://raw.githubusercontent.com/Deepikaa13/Fake-Job-Posting-Prediction/main/fake_job_postings.csv",
    "https://raw.githubusercontent.com/RohanBais/Fake-Job-Posting-Prediction/master/fake_job_postings.csv",
    "https://raw.githubusercontent.com/amruthjithrajvr/recruitment-scam/main/fake_job_postings.csv"
]

print("Searching candidate dataset URLs...")
success_url = None

for u in candidate_urls:
    try:
        req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                print("SUCCESSFUL URL:", u)
                success_url = u
                data = response.read()
                with open("fake_job_postings.csv", "wb") as f:
                    f.write(data)
                break
    except Exception as e:
        pass

if not success_url:
    print("Could not download via standard GitHub candidate list. Attempting fallback download...")
