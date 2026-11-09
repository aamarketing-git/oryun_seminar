"""
오륜미네랄 세미나 포스터 생성기 (서버용)
- 웹앱(상황실)의 스타일 A/B 좌표를 그대로 재현합니다.
- generate_poster(fields, style="a", out_path=..., photo_path=None) → PNG 파일 생성
"""
import os, io
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
RED = (192, 57, 43)
WHITE = (255, 255, 255)
BLACK = (17, 17, 17)

# 웹앱 STYLES 와 1:1 대응 (포스터 캔버스 640×904)
STYLES = {
    "a": {"bg": "styleA_bg.jpg", "date_top": 416, "date_left": 12, "date_fs": 35,
          "time_red": True, "place_top": 520, "fit_avail": 400,
          "circle": (336, 808), "map_c": (510, 745), "map_max": (209, 299)},
    "b": {"bg": "styleB_bg.jpg", "date_top": 416, "date_left": 12, "date_fs": 44,
          "time_red": False, "place_top": 520, "fit_avail": 400,
          "circle": (300, 748), "map_c": (500, 781), "map_max": (268, 190)},
}

_WD = ["월", "화", "수", "목", "금", "토", "일"]


def F(sz):
    return ImageFont.truetype(os.path.join(ASSETS, "Pretendard-Bold.otf"), sz)


def poster_date(s):
    """'2026-08-06' → '8월 6일 (목)'. 이미 포맷된 문자열이면 그대로."""
    if not s:
        return ""
    try:
        d = datetime.strptime(str(s)[:10], "%Y-%m-%d")
        return "%d월 %d일 (%s)" % (d.month, d.day, _WD[d.weekday()])
    except Exception:
        return str(s)


def poster_time(s):
    """'14:00' → '오후 2시'. 이미 한글이면 그대로."""
    if not s:
        return ""
    try:
        hh, mm = str(s).split(":")[:2]
        hh, mm = int(hh), int(mm)
        ap = "오전" if hh < 12 else "오후"
        h12 = hh % 12 or 12
        return "%s %d시%s" % (ap, h12, ("" if mm == 0 else " %d분" % mm))
    except Exception:
        return str(s)


def _outline(d, xy, t, font, fill, anchor="la"):
    x, y = xy
    for dx, dy in [(-2, -2), (2, -2), (-2, 2), (2, 2)]:
        d.text((x + dx, y + dy), t, font=font, fill=WHITE, anchor=anchor)
    d.text((x, y), t, font=font, fill=fill, anchor=anchor)


def _shadow(d, xy, t, font, fill, anchor="la"):
    x, y = xy
    d.text((x + 2, y + 2), t, font=font, fill=(0, 0, 0), anchor=anchor)
    d.text((x, y), t, font=font, fill=fill, anchor=anchor)


def _fit(d, t, base, mn, avail):
    fs = base
    while fs > mn and d.textlength(t, font=F(fs)) > avail:
        fs -= 1
    return fs


def _cover(img, W, H):
    w, h = img.size
    sc = max(W / w, H / h)
    img = img.resize((max(1, int(w * sc)), max(1, int(h * sc))), Image.LANCZOS)
    iw, ih = img.size
    left, top = (iw - W) // 2, (ih - H) // 2
    return img.crop((left, top, left + W, top + H))


def generate_poster(fields, style="a", out_path=None, photo_path=None):
    """
    fields: dict(date, time, venue, address, count)
    style:  "a"(네이비) | "b"(골프)
    photo_path: 우측 하단 프레임에 넣을 지도/건물 사진 (선택)
    """
    P = STYLES.get(style, STYLES["a"])
    im = Image.open(os.path.join(ASSETS, P["bg"])).convert("RGB").resize((640, 904), Image.LANCZOS)
    d = ImageDraw.Draw(im)

    # 지도/건물 (우측 하단 프레임, cover-fill + 흰 테두리)
    if photo_path and os.path.exists(photo_path):
        W, H = P["map_max"]
        cx, cy = P["map_c"]
        ph = _cover(Image.open(photo_path).convert("RGB"), W, H)
        x0, y0 = cx - W // 2, cy - H // 2
        im.paste(ph, (x0, y0))
        d.rectangle([x0 - 4, y0 - 4, x0 + W + 4, y0 + H + 4], outline=WHITE, width=4)

    # 일시 (날짜 + 시간 한 줄)
    dt = poster_date(fields.get("date", ""))
    tm = poster_time(fields.get("time", ""))
    dx, dy = P["date_left"], P["date_top"]
    _outline(d, (dx, dy), dt, F(P["date_fs"]), RED)
    if tm:
        tx = dx + d.textlength(dt, font=F(P["date_fs"])) + 10
        ty = dy + (P["date_fs"] - 28) // 2 + 2
        if P["time_red"]:
            _outline(d, (tx, ty), tm, F(28), RED)
        else:
            _shadow(d, (tx, ty), tm, F(28), WHITE)

    # 장소 (장소명 흰색 + 주소 붉은색)
    v = fields.get("venue", "") or ""
    ad = fields.get("address", "") or ""
    py = P["place_top"]
    vfs = _fit(d, v, 43, 24, P["fit_avail"])
    _shadow(d, (12, py), v, F(vfs), WHITE)
    if ad:
        afs = _fit(d, ad, 48, 24, P["fit_avail"])
        _outline(d, (12, py + vfs + 6), ad, F(afs), RED)

    # ~명 한정 말풍선
    cnt = fields.get("count", 0) or 0
    if cnt:
        cx, cy = P["circle"]
        d.ellipse([cx - 60, cy - 60, cx + 60, cy + 60], fill=WHITE, outline=RED, width=7)
        _shadow(d, (cx, cy - 15), "%d명" % int(cnt), F(40), RED, anchor="mm")
        _shadow(d, (cx, cy + 20), "한정", F(24), BLACK, anchor="mm")

    if out_path:
        im.save(out_path, "PNG")
        return out_path
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue()


if __name__ == "__main__":
    # 테스트
    fields = {"date": "2026-11-15", "time": "14:00",
              "venue": "국제건업건물 2층", "address": "인천시 부평구 동암남로 17,2층", "count": 50}
    generate_poster(fields, "a", os.path.join(HERE, "_test_a.png"))
    generate_poster(fields, "b", os.path.join(HERE, "_test_b.png"))
    print("saved _test_a.png, _test_b.png")
