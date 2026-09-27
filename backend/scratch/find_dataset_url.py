import urllib.request

urls = [
    "https://raw.githubusercontent.com/aditya-kushwaha/Fake-Job-Posting-Prediction/master/fake_job_postings.csv",
    "https://raw.githubusercontent.com/subhadiptamajumdar/Fake-Job-Posting-Prediction/master/fake_job_postings.csv",
    "https://raw.githubusercontent.com/dianaloz/Fake-Job-Posting/master/fake_job_postings.csv",
    "https://raw.githubusercontent.com/shivambansal/fake-job-postings/master/fake_job_postings.csv",
    "https://raw.githubusercontent.com/laxmimerit/All-CSV-ML-Files/master/fake_job_postings.csv",
    "https://raw.githubusercontent.com/GJU-CSE/Online-Recruitment-Fraud-Detection/main/fake_job_postings.csv",
    "https://raw.githubusercontent.com/jatin-kushwaha/Fake-Job-Postings-Prediction/master/fake_job_postings.csv",
    "https://raw.githubusercontent.com/amankharwal/Website-Data/master/fake_job_postings.csv",
    "https://raw.githubusercontent.com/RohanBais/Fake-Job-Posting-Prediction/master/fake_job_postings.csv",
    "https://raw.githubusercontent.com/Deepikaa13/Fake-Job-Posting-Prediction/main/fake_job_postings.csv",
    "https://raw.githubusercontent.com/Deepikaa13/Fake-Job-Posting-Prediction/master/fake_job_postings.csv",
    "https://raw.githubusercontent.com/AashishSaini/Fake-Job-Posting-Prediction/master/fake_job_postings.csv",
    "https://raw.githubusercontent.com/AashishSaini/Fake-Job-Posting-Prediction/main/fake_job_postings.csv",
    "https://raw.githubusercontent.com/sardend/Real-or-Fake-Job-Posting-Prediction/master/fake_job_postings.csv",
    "https://raw.githubusercontent.com/sardend/Real-or-Fake-Job-Posting-Prediction/main/fake_job_postings.csv",
    "https://raw.githubusercontent.com/sardend/Fake-Job-Postings-Prediction/main/fake_job_postings.csv"
]

found = False
for u in urls:
    try:
        req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
        res = urllib.request.urlopen(req)
        if res.status == 200:
            print("FOUND WORKING DATASET URL:", u)
            found = True
            # Save to local file
            content = res.read()
            with open("fake_job_postings.csv", "wb") as f:
                f.write(content)
            print("Downloaded file size:", len(content), "bytes")
            break
    except Exception as e:
        pass

if not found:
    print("NO_URL_FOUND")
