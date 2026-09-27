import httpx
import asyncio
import re

URLS_TO_TEST = [
    # HackIndia
    ("HackIndia", "https://hackindia.xyz"),
    ("HackIndia", "https://www.hackindia.xyz"),
    ("HackIndia", "https://hackindia.in"),
    
    # HCLTech
    ("HCLTech", "https://hcltech.com"),
    ("HCLTech", "https://www.hcltech.com"),
    ("HCLTech", "https://www.hcl.com"),
    
    # HAL
    ("HAL", "https://hal-india.co.in"),
    ("HAL", "https://www.hal-india.co.in"),
    ("HAL", "https://hal-india.com"),
    
    # Triangle Mind
    ("Triangle Mind", "https://trianglemind.com"),
    ("Triangle Mind", "https://www.trianglemind.com"),
    ("Triangle Mind", "https://trianglemind.in"),
]

async def probe_url(company, entered_url):
    client = httpx.AsyncClient(
        follow_redirects=True,
        timeout=15.0,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
        verify=False
    )
    
    try:
        response = await client.get(entered_url)
        final_url = str(response.url)
        status_code = response.status_code
        redirect_chain = [str(r.url) for r in response.history]
        
        html = response.text
        # Extract title
        title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else "No Title Found"
        title = re.sub(r'\s+', ' ', title)
        
        # Extract meta description
        desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']', html, re.IGNORECASE)
        if not desc_match:
            desc_match = re.search(r'<meta[^>]*content=["\'](.*?)["\'][^>]*name=["\']description["\']', html, re.IGNORECASE)
        meta_desc = desc_match.group(1).strip() if desc_match else ""
        meta_desc = re.sub(r'\s+', ' ', meta_desc)[:150]
        
        # Look for copyright or legal entity mentions
        copyright_match = re.search(r'(?:copyright|©|\(c\))\s*(?:20\d\d)?\s*([^<\.\n]+)', html, re.IGNORECASE)
        copyright_str = copyright_match.group(0).strip() if copyright_match else ""
        copyright_str = re.sub(r'\s+', ' ', copyright_str)[:100]

        return {
            "company": company,
            "entered_url": entered_url,
            "final_url": final_url,
            "status_code": status_code,
            "redirects": redirect_chain,
            "title": title,
            "meta_desc": meta_desc,
            "copyright": copyright_str,
            "error": None
        }
    except Exception as exc:
        return {
            "company": company,
            "entered_url": entered_url,
            "final_url": None,
            "status_code": None,
            "redirects": [],
            "title": None,
            "meta_desc": None,
            "copyright": None,
            "error": str(exc)
        }
    finally:
        await client.aclose()

async def main():
    print("Starting live URL probe validation...")
    results = []
    for company, url in URLS_TO_TEST:
        res = await probe_url(company, url)
        results.append(res)
        print(f"--- {company} ({url}) ---")
        if res["error"]:
            print(f"  Error: {res['error']}")
        else:
            print(f"  Status: {res['status_code']}")
            print(f"  Final URL: {res['final_url']}")
            print(f"  Redirects: {res['redirects']}")
            print(f"  Title: {res['title']}")
            print(f"  Copyright/Mention: {res['copyright']}")
        print()

if __name__ == "__main__":
    asyncio.run(main())
