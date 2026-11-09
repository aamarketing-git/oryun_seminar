"""
오륜미네랄 세미나 봇 — Vercel 웹훅 (PC 없이 24시간 동작)
- 텔레그램에서 세미나 정보를 보내면 포스터를 만들어 이미지로 답장합니다.
- GET  /api/telegram?setup=1  → 봇 웹훅을 자동 등록(최초 1회)
- POST /api/telegram          → 텔레그램이 보내는 업데이트 처리

Vercel 환경변수(필수): TG_TOKEN = @BotFather 봇 토큰
선택: TG_ALLOW = 허용 채팅ID(쉼표로 여러 개). 비우면 보낸 사람에게 그대로 답장.
"""
import os, json, io
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests
from poster import generate_poster, poster_date, poster_time

TOKEN = os.environ.get("TG_TOKEN", "").strip()
ALLOW = [x.strip() for x in os.environ.get("TG_ALLOW", "").split(",") if x.strip()]
API = "https://api.telegram.org/bot%s/" % TOKEN

HELP = (
    "📢 오륜미네랄 세미나 포스터 봇\n\n"
    "세미나 정보를 아래 순서로 '/'로 구분해 보내주세요:\n"
    "날짜 / 시간 / 장소 / 상세주소 / 인원 / 스타일(a 또는 b)\n\n"
    "예) 2026-11-15 / 14:00 / 국제건업건물 2층 / 인천시 부평구 동암남로 17,2층 / 50 / a\n\n"
    "• 스타일 a = 네이비 포스터, b = 골프장 포스터\n"
    "• 인원은 'NN명 한정' 말풍선 (0이면 표시 안 함)"
)


def send_text(chat, text):
    try:
        requests.post(API + "sendMessage", data={"chat_id": chat, "text": text}, timeout=20)
    except Exception:
        pass


def send_photo(chat, img_bytes, caption=""):
    requests.post(API + "sendPhoto", data={"chat_id": chat, "caption": caption},
                  files={"photo": ("poster.png", img_bytes, "image/png")}, timeout=40)


def parse(text):
    parts = [p.strip() for p in text.replace("\n", "/").split("/") if p.strip() != ""]
    if len(parts) < 3:
        return None
    f = {"date": parts[0], "time": parts[1], "venue": parts[2],
         "address": parts[3] if len(parts) > 3 else "", "count": 0}
    style = "a"
    if len(parts) > 4:
        digits = "".join(ch for ch in parts[4] if ch.isdigit())
        f["count"] = int(digits) if digits else 0
    if len(parts) > 5 and parts[5].lower() in ("a", "b"):
        style = parts[5].lower()
    return f, style


def handle_update(update):
    msg = update.get("message") or update.get("edited_message")
    if not msg:
        return
    chat = str(msg["chat"]["id"])
    if ALLOW and chat not in ALLOW:
        send_text(chat, "사용 권한이 없습니다. (채팅ID: %s)" % chat)
        return
    text = (msg.get("text") or "").strip()
    if not text:
        return
    if text in ("/start", "/help", "도움말"):
        send_text(chat, HELP + "\n\n(이 채팅 ID: %s)" % chat)
        return
    parsed = parse(text)
    if not parsed:
        send_text(chat, "형식을 인식하지 못했습니다.\n\n" + HELP)
        return
    f, style = parsed
    send_text(chat, "포스터 생성 중… (%s %s)" % (poster_date(f["date"]), poster_time(f["time"])))
    try:
        img = generate_poster(f, style)
        cap = ("📢 세미나 포스터\n🗓 %s %s\n📍 %s %s" % (
            poster_date(f["date"]), poster_time(f["time"]), f["venue"], f["address"])).strip()
        send_photo(chat, img, cap)
    except Exception as e:
        send_text(chat, "포스터 생성 오류: %s" % e)


class handler(BaseHTTPRequestHandler):
    def _ok(self, body="ok", code=200, ctype="text/plain; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def do_GET(self):
        q = parse_qs(urlparse(self.path).query)
        if not TOKEN:
            return self._ok("환경변수 TG_TOKEN 이 설정되지 않았습니다.", 500)
        if "setup" in q:
            host = self.headers.get("host", "")
            url = "https://%s/api/telegram" % host
            try:
                r = requests.get(API + "setWebhook", params={"url": url}, timeout=20).json()
                return self._ok("웹훅 등록 결과: %s\n등록 주소: %s" % (json.dumps(r, ensure_ascii=False), url))
            except Exception as e:
                return self._ok("웹훅 등록 실패: %s" % e, 500)
        return self._ok("오륜미네랄 세미나 봇이 작동 중입니다. 최초 1회 ?setup=1 로 웹훅을 등록하세요.")

    def do_POST(self):
        try:
            n = int(self.headers.get("content-length", 0))
            body = self.rfile.read(n) if n else b"{}"
            update = json.loads(body.decode("utf-8") or "{}")
            handle_update(update)
        except Exception:
            pass
        self._ok("ok")
