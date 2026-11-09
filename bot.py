"""
오륜미네랄 세미나 AI비서 — 텔레그램 대화형 봇
- 텔레그램에서 세미나 정보를 보내면 → 포스터를 생성해 이미지로 그대로 답장합니다.
- 추가 라이브러리 없이 표준 requests 롱폴링으로 동작합니다.

환경변수:
  TG_TOKEN  : @BotFather 로 받은 봇 토큰 (필수)
  TG_ALLOW  : (선택) 허용할 채팅 ID. 비우면 모두 허용.

입력 형식 (한 줄 또는 '/' 로 구분, 순서대로):
  날짜 / 시간 / 장소 / 상세주소 / 인원 / 스타일(a 또는 b)
예)
  2026-11-15 / 14:00 / 국제건업건물 2층 / 인천시 부평구 동암남로 17,2층 / 50 / a
"""
import os, sys, time, io, json, requests
from poster import generate_poster, poster_date, poster_time

TOKEN = os.environ.get("TG_TOKEN", "").strip()
ALLOW = [x.strip() for x in os.environ.get("TG_ALLOW", "").split(",") if x.strip()]
API = "https://api.telegram.org/bot%s/" % TOKEN

HELP = (
    "📢 오륜미네랄 세미나 포스터 봇\n\n"
    "세미나 정보를 아래 순서로 '/'(슬래시)로 구분해 보내주세요:\n"
    "날짜 / 시간 / 장소 / 상세주소 / 인원 / 스타일(a 또는 b)\n\n"
    "예시)\n"
    "2026-11-15 / 14:00 / 국제건업건물 2층 / 인천시 부평구 동암남로 17,2층 / 50 / a\n\n"
    "• 스타일 a = 네이비(물방울) 포스터, b = 골프장 포스터\n"
    "• 인원은 'NN명 한정' 말풍선에 들어갑니다 (0이면 표시 안 함)\n"
    "• 보내면 포스터 이미지를 바로 만들어 드립니다."
)


def send_text(chat, text):
    requests.post(API + "sendMessage", data={"chat_id": chat, "text": text}, timeout=30)


def send_photo(chat, img_bytes, caption=""):
    requests.post(API + "sendPhoto", data={"chat_id": chat, "caption": caption},
                  files={"photo": ("poster.png", img_bytes, "image/png")}, timeout=60)


def parse(text):
    parts = [p.strip() for p in text.replace("\n", "/").split("/")]
    parts = [p for p in parts if p != ""]
    if len(parts) < 3:
        return None
    f = {"date": parts[0], "time": parts[1] if len(parts) > 1 else "",
         "venue": parts[2] if len(parts) > 2 else "",
         "address": parts[3] if len(parts) > 3 else "",
         "count": 0}
    style = "a"
    if len(parts) > 4:
        try:
            f["count"] = int("".join(ch for ch in parts[4] if ch.isdigit()) or 0)
        except Exception:
            f["count"] = 0
    if len(parts) > 5 and parts[5].lower() in ("a", "b"):
        style = parts[5].lower()
    return f, style


def handle(msg):
    chat = str(msg["chat"]["id"])
    if ALLOW and chat not in ALLOW:
        send_text(chat, "이 봇을 사용할 권한이 없습니다. (채팅ID: %s)" % chat)
        return
    text = (msg.get("text") or "").strip()
    if not text:
        return
    if text in ("/start", "/help", "도움말"):
        send_text(chat, HELP + "\n\n(이 채팅의 ID: %s)" % chat)
        return
    parsed = parse(text)
    if not parsed:
        send_text(chat, "형식을 인식하지 못했습니다.\n\n" + HELP)
        return
    f, style = parsed
    send_text(chat, "포스터 생성 중… (%s %s)" % (poster_date(f["date"]), poster_time(f["time"])))
    try:
        img = generate_poster(f, style)  # bytes
        cap = "📢 세미나 포스터\n🗓 %s %s\n📍 %s %s" % (
            poster_date(f["date"]), poster_time(f["time"]), f["venue"], f["address"])
        send_photo(chat, img, cap.strip())
    except Exception as e:
        send_text(chat, "포스터 생성 오류: %s" % e)


def main():
    if not TOKEN:
        print("ERROR: 환경변수 TG_TOKEN 을 설정하세요."); sys.exit(1)
    print("봇 시작. @BotFather 봇과 대화를 시작하세요.")
    offset = None
    while True:
        try:
            r = requests.get(API + "getUpdates",
                             params={"timeout": 50, "offset": offset}, timeout=60)
            data = r.json()
            for up in data.get("result", []):
                offset = up["update_id"] + 1
                if "message" in up:
                    handle(up["message"])
        except Exception as e:
            print("poll error:", e); time.sleep(3)


if __name__ == "__main__":
    main()
