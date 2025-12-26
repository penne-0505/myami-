create table if not exists public.points (
  guild_id bigint not null,
  user_id bigint not null,
  points integer not null default 0,
  primary key (guild_id, user_id)
);

create table if not exists public.point_remove_permissions (
  guild_id bigint not null,
  user_id bigint not null,
  primary key (guild_id, user_id)
);

create table if not exists public.clan_register_settings (
  guild_id bigint primary key,
  channel_id bigint not null
);

create table if not exists public.role_buy_settings (
  guild_id bigint not null,
  role_id bigint not null,
  price integer not null,
  primary key (guild_id, role_id)
);

create or replace function public.ensure_points_schema()
returns void
language plpgsql
as $$
begin
  create table if not exists public.points (
    guild_id bigint not null,
    user_id bigint not null,
    points integer not null default 0,
    primary key (guild_id, user_id)
  );
  create table if not exists public.point_remove_permissions (
    guild_id bigint not null,
    user_id bigint not null,
    primary key (guild_id, user_id)
  );
  create table if not exists public.clan_register_settings (
    guild_id bigint primary key,
    channel_id bigint not null
  );
  create table if not exists public.role_buy_settings (
    guild_id bigint not null,
    role_id bigint not null,
    price integer not null,
    primary key (guild_id, role_id)
  );
end;
$$;

create or replace function public.add_points(
  p_guild_id bigint,
  p_user_id bigint,
  p_delta integer
)
returns integer
language plpgsql
as $$
declare
  new_points integer;
begin
  insert into public.points (guild_id, user_id, points)
  values (p_guild_id, p_user_id, 0)
  on conflict (guild_id, user_id) do nothing;

  update public.points
  set points = points + p_delta
  where guild_id = p_guild_id and user_id = p_user_id
  returning points into new_points;

  return new_points;
end;
$$;

create or replace function public.transfer_points(
  p_guild_id bigint,
  p_sender_id bigint,
  p_recipient_id bigint,
  p_points integer
)
returns boolean
language plpgsql
as $$
declare
  sender_points integer;
begin
  if p_points <= 0 then
    return false;
  end if;

  insert into public.points (guild_id, user_id, points)
  values (p_guild_id, p_sender_id, 0), (p_guild_id, p_recipient_id, 0)
  on conflict (guild_id, user_id) do nothing;

  select points into sender_points
  from public.points
  where guild_id = p_guild_id and user_id = p_sender_id
  for update;

  if sender_points < p_points then
    return false;
  end if;

  update public.points
  set points = points - p_points
  where guild_id = p_guild_id and user_id = p_sender_id;

  update public.points
  set points = points + p_points
  where guild_id = p_guild_id and user_id = p_recipient_id;

  return true;
end;
$$;

-- Migration: guild-scoped points (one-time)
-- 1) Add guild_id and update existing rows with the specified guild.
-- 2) Recreate primary keys for points and permissions.
-- NOTE: Replace the guild id if needed. This migration uses 746587719827980359.
-- Points table migration
-- alter table public.points add column if not exists guild_id bigint;
-- update public.points set guild_id = 746587719827980359 where guild_id is null;
-- alter table public.points alter column guild_id set not null;
-- alter table public.points drop constraint if exists points_pkey;
-- alter table public.points add primary key (guild_id, user_id);
--
-- Point remove permissions migration
-- alter table public.point_remove_permissions add column if not exists guild_id bigint;
-- update public.point_remove_permissions
-- set guild_id = 746587719827980359
-- where guild_id is null;
-- alter table public.point_remove_permissions alter column guild_id set not null;
-- alter table public.point_remove_permissions drop constraint if exists point_remove_permissions_pkey;
-- alter table public.point_remove_permissions add primary key (guild_id, user_id);

-- Drop legacy point tables (use with caution)
-- drop table if exists public.point_remove_permissions;
-- drop table if exists public.points;
