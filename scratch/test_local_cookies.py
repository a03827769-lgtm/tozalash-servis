import browser_cookie3
import os

def extract_cookies():
    try:
        print("Extracting from Chrome...")
        cj = browser_cookie3.chrome(domain_name=".google.com")
        psid = None
        psidts = None
        for cookie in cj:
            if cookie.name == "__Secure-1PSID":
                psid = cookie.value
            elif cookie.name == "__Secure-1PSIDTS":
                psidts = cookie.value
        print(f"Chrome PSID: {psid[:10]}... PSIDTS: {psidts[:10]}...")
    except Exception as e:
        print("Chrome error:", e)

extract_cookies()
