"""
오륜미네랄 세미나 — 주간 리포트 자동 전송
- Supabase(app_state)에서 세미나 데이터를 읽어
  '이번 주 세미나 일정' + '다음 주 예정·준비사항' 리포트를 만들어 텔레그램으로 전송합니다.
- GitHub Actions(무료) 스케줄로 매주 자동 실행하도록 설계되었습니다.

환경변수:
  TG_TOKEN   : 텔레그램 봇 토큰 (필수)
  TG_CHAT    : 리포트를 받을 채팅/단톡방 ID (필수)
  SUPA_URL   : https://remgykeiwxpjhcocezin.supabase.co
  SUPA_KEY   : sb_publishable_... (앱에서 쓰는 publishable key)
"""
import os, requests
from datetime import datetime, timedelta, timezone

TOKEN = os.environ.get("TG_TOKEN", "").strip()
CHAT = os.environ.get("TG_CHAT", "").strip()
SUPA_URL = os.environ.get("SUPA_URL", "https://remgykeiwxpjhcocezin.supabase.co").strip()
SUPA_KEY = os.environ.get("SUPA_KEY", "").strip()
KST = timezone(timedelta(hours=9))
STATUS = {"requested": "요청", "confirmed": "확정", "done": "완료", "canceled": "취소"}


def load_db():
    url = SUPA_URL.rstrip("/") + "/rest/v1/app_state"
    r = requests.get(url, params={"id": "eq.main", "select": "data"},
                     headers={"apikey": SUPA_KEY, "Authorization": "Bearer " + SUPA_KEY},
                     timeout=30)
    r.raise_for_status()
    rows = r.json()
    return (rows[0]["data"] if rows else {}) or {}


def center_name(db, cid):
    for c in db.get("centers", []):
        if c.get("id") == cid:
            return c.get("name", "")
    return ""


def week_bounds(base, offset_weeks=0):
    monday = base - timedelta(days=base.weekday()) + timedelta(weeks=offset_weeks)
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    return monday.date(), (monday + timedelta(days=6)).date()


def fmt_line(db, s):
    try:
        d = datetime.strptime(s.get("date", "")[:10], "%Y-%m-%d")
        ds = "%d/%d(%s)" % (d.month, d.day, ["월", "화", "수", "목", "금", "토", "일"][d.weekday()])
    except Exception:
        ds = s.get("date", "?")
    tm = s.get("time", "")
    cn = center_name(db, s.get("centerId"))
    venue = s.get("venue", "")
    st = STATUS.get(s.get("status", ""), s.get("status", ""))
    cnt = s.get("count", 0)
    extra = (" · %d명" % cnt) if cnt else ""
    return "• %s %s  %s%s  [%s]%s" % (ds, tm, cn, (" " + venue if venue else ""), st, extra)


def build_report(db):
    now = datetime.now(KST)
    sems = [s for s in db.get("seminars", []) if s.get("date")]
    tw_s, tw_e = week_bounds(now, 0)
    nw_s, nw_e = week_bounds(now, 1)

    def in_range(s, a, b):
        try:
            d = datetime.strptime(s["date"][:10], "%Y-%m-%d").date()
            return a <= d <= b
        except Exception:
            return False

    this_week = sorted([s for s in sems if in_range(s, tw_s, tw_e)], key=lambda s: (s["date"], s.get("time", "")))
    next_week = sorted([s for s in sems if in_range(s, nw_s, nw_e)], key=lambda s: (s["date"], s.get("time", "")))

    lines = []
    lines.append("📅 오륜미네랄 세미나 주간 리포트")
    lines.append("(%s 기준)" % now.strftime("%Y-%m-%d"))
    lines.append("")
    lines.append("■ 이번 주 세미나 (%s~%s) : %d건" % (tw_s.strftime("%m/%d"), tw_e.strftime("%m/%d"), len(this_week)))
    lines += [fmt_line(db, s) for s in this_week] or ["• (없음)"]
    lines.append("")
    lines.append("■ 다음 주 예정 (%s~%s) : %d건" % (nw_s.strftime("%m/%d"), nw_e.strftime("%m/%d"), len(next_week)))
    lines += [fmt_line(db, s) for s in next_week] or ["• (없음)"]

    # 준비사항 체크 (다음 주 중 미확정/포스터 미완료)
    todo = []
    for s in next_week:
        cn = center_name(db, s.get("centerId"))
        if s.get("status") == "requested":
            todo.append("· %s: 일정 확정 필요" % cn)
        if not s.get("posterReady"):
            todo.append("· %s: 포스터 준비 필요" % cn)
    if todo:
        lines.append("")
        lines.append("■ 준비사항")
        lines += todo
    return "\n".join(lines)


def main():
    if not (TOKEN and CHAT and SUPA_KEY):
        print("ERROR: TG_TOKEN, TG_CHAT, SUPA_KEY 환경변수가 필요합니다."); return
    db = load_db()
    text = build_report(db)
    requests.post("https://api.telegram.org/bot%s/sendMessage" % TOKEN,
                  data={"chat_id": CHAT, "text": text}, timeout=30)
    print("리포트 전송 완료\n\n" + text)


if __name__ == "__main__":
    main()
