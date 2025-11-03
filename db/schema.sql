-- Supabase standaard extensie voor UUID's
create extension if not exists "pgcrypto";


-- ===== COMPANY =====
create table if not exists company (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  email text unique,
  created_at timestamptz not null default now()
);

-- ===== KLANT =====
create table if not exists klant (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references company(id) on delete cascade,
  name text not null,
  email text,
  address text,
  created_at timestamptz not null default now()
);

-- ===== PREFERENCES =====
create table if not exists preferences (
  id uuid primary key default gen_random_uuid(),
  klant_id uuid not null references klant(id) on delete cascade,
  min_price numeric(12,2),
  max_price numeric(12,2),
  min_area_m2 int,
  max_area_m2 int,
  location text,
  zoning_allowed text,
  verkavelingstype text,
  soil_pref text,
  created_at timestamptz not null default now()
);

-- ===== BOUWGROND =====
create table if not exists bouwgrond (
  id uuid primary key default gen_random_uuid(),
  address text,
  postcode text,
  area_m2 int,
  asking_price numeric(12,2),
  zoning text,
  owner_name text,
  soil text,
  verkavelingstype text,
  status grond_status_enum default 'listed',
  created_at timestamptz not null default now()
);

-- ===== MATCH =====
create table if not exists match (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references company(id) on delete cascade,
  klant_id uuid not null references klant(id) on delete cascade,
  bouwgrond_id uuid not null references bouwgrond(id) on delete cascade,
  preference_id_used uuid references preferences(id) on delete set null,
  score int check (score between 0 and 100),
  status match_status_enum default 'suggested',
  reasons text,
  created_at timestamptz not null default now(),
  unique (klant_id, bouwgrond_id)
);
