-- 오륜미네랄 · DMAX 세미나 운영 통제실
-- Supabase 실시간 데이터 공유용 스키마
-- 사용법: Supabase 프로젝트 → SQL Editor → 아래 전체 붙여넣고 Run

-- 1) 앱 상태를 한 행(JSON)으로 저장하는 테이블
create table if not exists public.app_state (
  id          text primary key,
  data        jsonb not null default '{}'::jsonb,
  updated_at  timestamptz default now()
);

-- 2) 행 수준 보안 켜기
alter table public.app_state enable row level security;

-- 3) (소규모 내부 운영용) 익명 anon 키로 읽기/쓰기 허용
--    ⚠️ anon 키를 아는 사람은 누구나 읽고 쓸 수 있습니다. 내부 팀용으로만 쓰세요.
--    보안을 강화하려면 이 정책을 지우고 Supabase Auth(로그인) 기반 정책으로 교체하세요.
drop policy if exists app_state_rw on public.app_state;
create policy app_state_rw on public.app_state
  for all
  to anon, authenticated
  using (true)
  with check (true);

-- 4) 실시간(Realtime) 브로드캐스트 활성화 — 다른 사람의 변경이 즉시 반영됨
--    이미 추가되어 있으면 에러가 날 수 있는데, 그럴 땐 이 줄만 건너뛰면 됩니다.
alter publication supabase_realtime add table public.app_state;

-- 완료. 이제 index.html 상단의 window.SUPA_URL / window.SUPA_KEY 에
-- 프로젝트 URL 과 anon public key 를 넣고 다시 배포하면 실시간 공유가 켜집니다.
