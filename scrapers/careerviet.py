"""CareerViet — parse HTML trang danh sách (50 job/trang)."""
import re

from bs4 import BeautifulSoup

from .common import get, slugify

BASE = "https://careerviet.vn"
# Từ khoá chỉ chạy được khi KHÔNG kèm bộ lọc tỉnh (thêm "-l8" thì bị bỏ qua từ khoá)
# → lấy toàn quốc rồi lọc địa điểm ở phía mình. Chỉ dùng từ khoá đơn (cụm từ ra 0 kết quả).
URL_P1 = BASE + "/viec-lam/{slug}-k-vi.html"
URL_PN = BASE + "/viec-lam/{slug}-k-trang-{page}-vi.html"
UPDATED_RE = re.compile(r"Cập nhật\s*:\s*([\d-]+)")


def fetch(cfg: dict) -> list[dict]:
    jobs = []
    max_pages = cfg.get("max_pages", 4)
    for query in cfg.get("queries", []):
        slug = slugify(query)
        seen = set()
        for page in range(1, max_pages + 1):
            url = URL_P1.format(slug=slug) if page == 1 else URL_PN.format(slug=slug, page=page)
            soup = BeautifulSoup(get(url).text, "html.parser")
            fresh = 0
            for card in soup.select("div.job-item"):
                link = card.select_one("a.job_link")
                if not link:
                    continue
                job_id = link.get("data-id") or link.get("href")
                if job_id in seen:
                    continue
                seen.add(job_id)
                fresh += 1
                company = card.select_one(".company-name")
                location = card.select_one(".location")
                salary = card.select_one(".salary")
                time_txt = card.select_one(".time")
                m = UPDATED_RE.search(time_txt.get_text(" ", strip=True)) if time_txt else None
                href = link.get("href", "")
                jobs.append({
                    "id": f"careerviet:{job_id}",
                    "source": "CareerViet",
                    "title": link.get_text(strip=True),
                    "company": company.get_text(strip=True) if company else "",
                    "url": href if href.startswith("http") else BASE + href,
                    # thuộc tính title có dạng "Đồng Nai | Hồ Chí Minh"
                    "location": (location.get("title") or location.get_text(strip=True))
                                .replace("|", ",") if location else "",
                    "salary": (salary.get_text(strip=True).replace("Lương:", "").strip()
                               if salary else ""),
                    "posted": m.group(1) if m else "",
                    "extra": "",
                })
            if fresh == 0:
                break
    return jobs
