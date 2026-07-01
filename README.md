# 오륜미네랄 · DMAX 세미나 운영 통제실 — 배포 가이드

관리자(본사)와 센터장이 세미나 요청·발송·입금·문의·포스터를 한곳에서 관리하는 웹앱입니다.

## 파일 구성
- **index.html** — 앱 본체. 이 파일 하나만 있으면 실행됩니다. (Vercel 배포 시 자동으로 첫 화면이 됩니다)
- **supabase_schema.sql** — 실시간 데이터 공유용 데이터베이스 스키마
- **App.jsx** — Vite/Next 프로젝트에 넣을 React 소스 (직접 빌드해서 쓰실 분용)

---

## 먼저 알아둘 점 — "서로 소통"에는 데이터베이스가 필요합니다

깃허브 + Vercel 배포는 **누구나 웹에서 열 수 있게** 해줍니다. 하지만 아무 설정도 안 하면 데이터가 **각자 브라우저에만 저장(localStorage)** 되어, 관리자와 센터장이 서로의 내용을 볼 수 없습니다(= 데모 모드).

**서로 공유·소통하려면** 아래 3단계 중 마지막 "Supabase 연결"까지 해야 합니다.

---

## 1단계. 깃허브에 올리기

```bash
# 이 폴더에서
git init
git add index.html supabase_schema.sql App.jsx README.md
git commit -m "세미나 운영 통제실"
git branch -M main
git remote add origin https://github.com/<본인아이디>/<저장소이름>.git
git push -u origin main
```
(웹 깃허브에서 새 저장소를 만든 뒤 파일을 드래그해 올려도 됩니다.)

## 2단계. Vercel 배포

1. https://vercel.com 로그인 → **Add New → Project**
2. 방금 만든 깃허브 저장소를 **Import**
3. Framework Preset은 **Other**(정적 사이트)로 두고 **Deploy**
4. 배포가 끝나면 `https://<프로젝트>.vercel.app` 주소로 접속됩니다.

이 상태로도 앱은 열리지만, 아직 **데이터는 공유되지 않습니다**(데모 모드).

## 3단계. Supabase 연결 — 실시간 공유 켜기 ★

1. https://supabase.com 에서 무료 프로젝트 생성 (Region은 **Seoul** 권장)
2. 좌측 **SQL Editor** → `supabase_schema.sql` 내용을 붙여넣고 **Run**
3. 좌측 **Project Settings → API** 에서 두 값 복사
   - **Project URL** (예: `https://xxxx.supabase.co`)
   - **anon public** key (`eyJ...` 로 시작하는 긴 문자열)
4. `index.html` 맨 위의 이 부분에 붙여넣기:
   ```html
   <script>
     window.SUPA_URL = "여기에 Project URL";
     window.SUPA_KEY = "여기에 anon public key";
   </script>
   ```
5. 저장 → `git commit` → `git push` → Vercel이 자동으로 다시 배포합니다.

이제 관리자·센터장이 어느 기기에서 접속해도 **같은 데이터를 실시간으로** 보고 함께 씁니다.

---

## 로그인 계정
- **관리자**: 아이디 `admin` / 비번 `admin1234` (앱 안 ⚙ 설정에서 변경)
- **센터장**: 앱의 "센터장 등록"에서 이름·전화번호·센터로 등록 → **이름 + 전화번호 뒤 4자리**로 로그인
- 데모 센터장: 이름 `포항센터장` / 뒤 4자리 `0404`

## 보안 안내
- 지금 스키마는 **anon 키로 읽기/쓰기를 허용**하는 소규모 내부용 설정입니다. anon 키가 공개되면 누구나 접근할 수 있으니 **팀 내부용으로만** 쓰세요.
- 로그인·비밀번호는 현재 앱 안에서만 확인하는 간단한 방식입니다. 외부 공개·민감 정보가 있다면 Supabase Auth 등 서버 인증으로 강화하시길 권합니다.
- 오륜미네랄은 **일반식품**입니다. 마케팅·문자에 질병 예방·치료·면역 등의 표현을 넣지 마세요(식품표시광고법).

## 참고 — 실시간 동기화 방식
앱 전체 상태를 `app_state` 테이블의 한 행(JSON)으로 저장하고, Supabase Realtime으로 변경을 즉시 반영합니다(마지막 저장 우선). 센터 수십 개 규모까지는 충분하며, 더 큰 동시 편집이 필요하면 테이블을 세미나/문의별로 분리하는 확장이 필요합니다.
