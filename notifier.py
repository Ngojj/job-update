"""Gửi thông báo job mới về Telegram."""
import html
import os
import time
from datetime import datetime, timedelta, timezone

import requests

MAX_LEN = 3800  # dưới giới hạn 4096 ký tự/tin nhắn của Telegram
VN_TZ = timezone(timedelta(hours=7))  # giờ Việt Nam (GitHub Actions chạy giờ UTC)


def _format_job(job: dict) -> str:
    title = html.escape(job.get("title", ""))
    company = html.escape(job.get("company", ""))
    lines = [f"🆕 <a href=\"{html.escape(job.get('url', ''))}\"><b>{title}</b></a>"]
    info = f"🏢 {company}" if company else ""
    if job.get("source"):
        info += f" ({job['source']})" if info else f"({job['source']})"
    if info:
        lines.append(info)
    detail = []
    if job.get("location"):
        detail.append(f"📍 {html.escape(job['location'])}")
    if job.get("salary"):
        detail.append(f"💰 {html.escape(job['salary'])}")
    if job.get("posted"):
        detail.append(f"🗓 Đăng: {html.escape(job['posted'])}")
    if detail:
        lines.append(" | ".join(detail))
    return "\n".join(lines)


def send_jobs(jobs: list[dict], mode: str = "new", warnings: list[str] | None = None) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise RuntimeError(
            "Thiếu TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID trong biến môi trường."
        )

    now = datetime.now(VN_TZ).strftime("%H:%M %d/%m/%Y")
    if mode == "all":
        title = f"💼 <b>{len(jobs)} việc làm Intern/Fresher đang tuyển</b>"
    else:
        title = f"💼 <b>Có {len(jobs)} việc làm Intern/Fresher mới!</b>"
    header = f"{title}\n🕐 Quét lúc {now}\n"
    if warnings:
        # Báo rõ nguồn nào không quét được để biết danh sách có thể chưa đầy đủ
        header += f"⚠️ Không quét được: {html.escape(', '.join(warnings))}\n"
    blocks = [_format_job(j) for j in jobs]

    # Gom nhiều job vào ít tin nhắn nhất có thể (mỗi tin < 4096 ký tự)
    messages, current = [], header
    for block in blocks:
        if len(current) + len(block) + 2 > MAX_LEN:
            messages.append(current)
            current = block
        else:
            current += "\n\n" + block
    messages.append(current)

    for i, text in enumerate(messages):
        if i:
            time.sleep(1.1)  # Telegram giới hạn ~1 tin/giây mỗi chat
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=25,
        )
        if not r.ok:
            raise RuntimeError(f"Telegram API lỗi {r.status_code}: {r.text[:300]}")
