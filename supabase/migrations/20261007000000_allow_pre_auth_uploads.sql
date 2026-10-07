-- Phase 3 uploads precede Supabase Auth (Phase 10). The trusted backend
-- records these as unowned; authenticated ownership remains enforced by RLS.
alter table public.uploads alter column user_id drop not null;
