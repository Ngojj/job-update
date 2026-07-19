"""Job Alert Bot — quét các trang tuyển dụng, lọc job Intern/Fresher
(software/data/AI) và báo về Telegram.

Cách chạy:
    python main.py            # chạy thật: gửi Telegram + ghi nhớ job đã gửi
    python main.py --dry-run  # chạy thử: chỉ in ra màn hình, không gửi, không ghi nhớ
"""
import argparse
import os
import sys

import yaml

from filters import JobFilter
from notifier import send_jobs
from scrapers import SCRAPERS
from storage import load_seen, mark_seen, save_seen

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="In kết quả ra màn hình, không gửi Telegram, không lưu trạng thái")
    args = parser.parse_args()

    with open(CONFIG_FILE, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # 1. Quét từng nguồn (nguồn nào lỗi thì bỏ qua, không làm sập cả job)
    all_jobs, errors = [], []
    for name, source_cfg in cfg.get("sources", {}).items():
        if not source_cfg.get("enabled", False):
            continue
        try:
            jobs = SCRAPERS[name](source_cfg)
            print(f"[{name}] lấy được {len(jobs)} job")
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"[{name}] LỖI: {type(e).__name__}: {e}", file=sys.stderr)
            errors.append(name)

    # 2. Khử trùng lặp giữa các query/nguồn
    unique = {j["id"]: j for j in all_jobs}
    print(f"Tổng cộng {len(unique)} job (đã khử trùng lặp)")

    # 3. Lọc theo level + ngành + địa điểm
    job_filter = JobFilter(cfg)
    matched = [j for j in unique.values() if job_filter.matches(j)]
    print(f"Khớp bộ lọc Intern/Fresher: {len(matched)} job")

    # 4. Chọn job cần báo theo chế độ:
    #    all = toàn bộ job đang tuyển | new = chỉ job chưa từng báo
    mode = cfg.get("report_mode", "new")
    seen = load_seen()
    if mode == "all":
        new_jobs = matched
        print(f"Chế độ 'all': báo toàn bộ {len(new_jobs)} job đang tuyển")
    else:
        new_jobs = [j for j in matched if j["id"] not in seen]
        print(f"Job mới chưa từng báo: {len(new_jobs)}")

    if args.dry_run:
        for j in new_jobs:
            print(f"  [{j['source']}] {j['title']} — {j['company']}"
                  f" | {j['location']} | {j['salary']} | {j['url']}")
        return 0

    # 5. Gửi Telegram (giới hạn số job mỗi lần để tránh spam)
    cap = cfg.get("max_new_per_run", 20)
    to_send = new_jobs[:cap]
    if len(new_jobs) > cap:
        print(f"Chỉ gửi {cap}/{len(new_jobs)} job (giới hạn max_new_per_run)")
    if to_send:
        send_jobs(to_send, mode=mode)
        print(f"Đã gửi {len(to_send)} job về Telegram")
    else:
        print("Không có job mới — không gửi gì")

    # 6. Ghi nhớ TẤT CẢ job khớp bộ lọc (kể cả phần bị cắt bởi cap,
    #    để lần đầu chạy không dồn backlog sang các lần sau)
    for j in matched:
        if j["id"] not in seen:
            mark_seen(seen, j["id"])
    save_seen(seen, cfg.get("seen_retention_days", 60))

    return 1 if errors and not all_jobs else 0


if __name__ == "__main__":
    sys.exit(main())
