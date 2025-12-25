create table if not exists public.points (
  user_id bigint primary key,
  points integer not null default 0
);

create table if not exists public.point_remove_permissions (
  user_id bigint primary key
);

create or replace function public.ensure_points_schema()
returns void
language plpgsql
as $$
begin
  create table if not exists public.points (
    user_id bigint primary key,
    points integer not null default 0
  );
  create table if not exists public.point_remove_permissions (
    user_id bigint primary key
  );
end;
$$;

create or replace function public.add_points(p_user_id bigint, p_delta integer)
returns integer
language plpgsql
as $$
declare
  new_points integer;
begin
  insert into public.points (user_id, points)
  values (p_user_id, 0)
  on conflict (user_id) do nothing;

  update public.points
  set points = points + p_delta
  where user_id = p_user_id
  returning points into new_points;

  return new_points;
end;
$$;

create or replace function public.transfer_points(
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

  insert into public.points (user_id, points)
  values (p_sender_id, 0), (p_recipient_id, 0)
  on conflict (user_id) do nothing;

  select points into sender_points
  from public.points
  where user_id = p_sender_id
  for update;

  if sender_points < p_points then
    return false;
  end if;

  update public.points
  set points = points - p_points
  where user_id = p_sender_id;

  update public.points
  set points = points + p_points
  where user_id = p_recipient_id;

  return true;
end;
$$;
