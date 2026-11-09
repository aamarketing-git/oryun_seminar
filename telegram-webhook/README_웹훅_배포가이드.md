# 오륜미네랄 세미나 봇 — PC 없이 24시간 (Vercel 웹훅)

내 컴퓨터가 꺼져 있어도, 모바일 텔레그램에서 세미나 정보를 보내면 포스터를 받습니다.
앱이 이미 Vercel에 올라가 있으니 **같은 저장소에 얹기만** 하면 됩니다. **추가 비용 없음.**

---

## 들어가는 파일 (저장소에 추가)
아래 구조 그대로 **상황실 깃허브 저장소**에 올립니다. (index.html 등 기존 파일은 그대로 두세요)
```
api/
  telegram.py        ← 봇 (웹훅)
  poster.py          ← 포스터 생성기
  assets/            ← 배경 2종 + 폰트
    styleA_bg.jpg
    styleB_bg.jpg
    Pretendard-Bold.otf
requirements.txt     ← (저장소 루트)
vercel.json          ← (저장소 루트)
```
> 이미 루트에 `requirements.txt` 나 `vercel.json` 이 있으면 덮어쓰지 말고 내용을 합쳐 주세요. (대개 없습니다)

---

## 설치 순서 (약 10분, 한 번만)

### 1) 파일 올리기
위 파일들을 저장소에 추가하고 평소처럼 배포(푸시)합니다. Vercel이 자동으로 다시 배포합니다.

### 2) 봇 토큰 등록 (Vercel 환경변수)
1. vercel.com → 이 프로젝트(oryun-seminar) → **Settings → Environment Variables**
2. **Add New** 로 추가:
   - Name: `TG_TOKEN`
   - Value: @BotFather 봇 토큰 (예: `7812345678:AAH...xyz`)
   - (선택) `TG_ALLOW` : 내 채팅ID `5451048765` — 넣으면 나만 사용 가능. 비우면 누구나 봇에 보내면 답장.
3. 저장 후 **Deployments → 가장 최근 배포 → ⋯ → Redeploy** 로 한 번 재배포 (환경변수 반영).

### 3) 웹훅 등록 (최초 1회)
브라우저에서 아래 주소를 한 번 엽니다:
```
https://oryun-seminar-jade.vercel.app/api/telegram?setup=1
```
`"ok":true` 와 `웹훅 등록 결과 ...` 가 보이면 성공입니다.

### 4) 사용
텔레그램에서 봇에게 보냅니다:
```
2026-11-15 / 14:00 / 국제건업건물 2층 / 인천시 부평구 동암남로 17,2층 / 50 / a
```
→ 순서: **날짜 / 시간 / 장소 / 상세주소 / 인원 / 스타일(a 또는 b)**
→ 포스터 이미지를 바로 보내줍니다. (`/help` 로 사용법)

**이제 PC를 꺼도 모바일에서 언제든 받을 수 있습니다.**

---

## 자주 막히는 곳
- **봇이 답이 없다** → 3) 웹훅 등록을 안 했거나, 2) 재배포를 안 해 `TG_TOKEN`이 반영 안 된 경우. `?setup=1` 을 다시 열어 `ok:true` 확인.
- **?setup=1 에서 TG_TOKEN 없음 오류** → 환경변수 저장 후 **Redeploy** 를 해야 반영됩니다.
- **특정 사람만 쓰게** 하려면 `TG_ALLOW` 에 채팅ID를 넣으세요(쉼표로 여러 명).
- 포스터가 `api/assets` 의 배경·폰트를 사용하므로 assets 폴더가 함께 올라가야 합니다. (`vercel.json` 의 includeFiles 가 자동 포함)

## 바꾸고 싶을 때
- 배경·좌표를 바꾸려면 `api/poster.py` 의 STYLES 값과 `api/assets` 이미지를 교체하면 됩니다. (앱과 동일한 좌표계: 캔버스 640×904)
