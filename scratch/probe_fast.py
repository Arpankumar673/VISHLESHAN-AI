import urllib.request
import urllib.parse
import ssl
import re

URLS = [
    ("HackIndia", "https://hackindia.xyz"),
    ("HackIndia", "https://www.hackindia.xyz"),
    ("HackIndia", "https://hackindia.in"),
    ("HCLTech", "https://www.hcltech.com"),
    ("HCLTech", "https://hcltech.com"),
    ("HAL", "https://hal-india.co.in"),
    ("HAL", "https://www.hal-india.co.in"),
    ("Triangle Mind", "https://trianglemind.com"),
    ("Triangle Mind", "https://www.trianglemind.com"),
]

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
}

for comp, url in URLS:
    req = urllib.request.Request(url, headers=headers)
    try:
        res = urllib.request.urlopen(req, context=ctx, timeout=10)
        final_url = res.geturl()
        code = res.getcode()
        body = res.read(15000).decode('utf-8', errors='ignore')
        
        title_m = re.search(r'<title>(.*?)</title>', body, re.IGNORECASE | re.DOTALL)
        title = title_m.group(1).strip() if title_m else "No Title"
        title = re.sub(r'\s+', ' ', title)
        
        print(f"COMP: {comp} | ENTERED: {url} | FINAL: {final_url} | CODE: {code} | TITLE: {title}")
    except Exception as e:
        print(f"COMP: {comp} | ENTERED: {url} | ERROR: {e}")
