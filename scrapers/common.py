import time

import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    ),
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
}
TIMEOUT = 25


def request(method: str, url: str, retries: int = 3, **kwargs) -> requests.Response:
    """requests có retry (lỗi mạng / 429 / 5xx) để một lần chập chờn không làm mất cả nguồn."""
    kwargs.setdefault("headers", HEADERS)
    kwargs.setdefault("timeout", TIMEOUT)
    last = None
    for attempt in range(retries):
        try:
            r = requests.request(method, url, **kwargs)
            if r.status_code == 429 or r.status_code >= 500:
                last = requests.HTTPError(f"{r.status_code} for {url}", response=r)
            else:
                r.raise_for_status()
                return r
        except (requests.ConnectionError, requests.Timeout) as e:
            last = e
        time.sleep(2 * (attempt + 1))
    raise last


def get(url: str, **kwargs) -> requests.Response:
    return request("GET", url, **kwargs)


def post(url: str, **kwargs) -> requests.Response:
    return request("POST", url, **kwargs)


def slugify(text: str) -> str:
    """'Thực tập sinh' -> 'thuc-tap-sinh' (dùng dựng URL tìm kiếm)."""
    import re
    import unicodedata
    t = text.replace("đ", "d").replace("Đ", "D")
    t = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
