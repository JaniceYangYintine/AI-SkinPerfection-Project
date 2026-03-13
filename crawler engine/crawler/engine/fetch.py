import time
import random
import requests

class Fetcher:
    def __init__(self, *, delay_range=(0.8, 1.8), timeout=15):
        self.delay_range = delay_range
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        })

    def get(self, url: str) -> str:
        time.sleep(random.uniform(*self.delay_range))
        r = self.session.get(url, timeout=self.timeout)
        r.raise_for_status()
        # Normalize encoding to avoid mojibake on sites with missing headers.
        if not r.encoding or r.encoding.lower() == "iso-8859-1":
            r.encoding = r.apparent_encoding or "utf-8"
        return r.text
