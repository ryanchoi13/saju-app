-- 운세의신 profiles
-- Supabase SQL Editor에서 실행하세요. 백엔드는 SERVICE_ROLE 키로 저장합니다.

create table if not exists public.profiles (
  id uuid primary key default gen_random_uuid(),
  nickname text not null,
  gender text not null check (gender in ('male', 'female')),
  calendar_type text not null default 'solar' check (calendar_type in ('solar', 'lunar')),
  is_leap_month boolean not null default false,
  birth_date date not null,
  birth_time time,
  time_unknown boolean not null default false,
  love_status text not null default 'solo',
  career_status text not null default 'employee',
  created_at timestamptz not null default now()
);

alter table public.profiles enable row level security;
