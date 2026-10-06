create extension if not exists vector with schema extensions;

create table public.products (
 id uuid primary key default gen_random_uuid(), name text not null check(length(trim(name))>0),
 brand text, category text, model text, description text, color text, gender text, image_url text,
 created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table public.product_images (
 id uuid primary key default gen_random_uuid(), product_id uuid not null references public.products on delete cascade,
 image_url text not null, image_type text not null default 'catalog', created_at timestamptz not null default now()
);
-- Leave dimension unconstrained until an embedding model is selected in Phase 6.
create table public.product_embeddings (
 id uuid primary key default gen_random_uuid(), product_id uuid not null references public.products on delete cascade,
 embedding extensions.vector not null, embedding_type text not null, model_name text not null,
 created_at timestamptz not null default now(), unique(product_id,embedding_type,model_name)
);
create table public.retailers (
 id uuid primary key default gen_random_uuid(), name text not null unique, website text, logo_url text,
 created_at timestamptz not null default now()
);
create table public.retailer_products (
 id uuid primary key default gen_random_uuid(), product_id uuid not null references public.products on delete cascade,
 retailer_id uuid not null references public.retailers on delete cascade, retailer_product_name text not null,
 product_url text, external_product_id text, current_price numeric(12,2) check(current_price is null or current_price>=0),
 currency varchar(3) not null default 'USD' check(currency ~ '^[A-Z]{3}$'), availability text,
 created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
 unique(retailer_id,external_product_id)
);
create table public.price_history (
 id uuid primary key default gen_random_uuid(), retailer_product_id uuid not null references public.retailer_products on delete cascade,
 price numeric(12,2) not null check(price>=0), currency varchar(3) not null check(currency ~ '^[A-Z]{3}$'),
 availability text, recorded_at timestamptz not null default now()
);
create table public.uploads (
 id uuid primary key default gen_random_uuid(), user_id uuid not null references auth.users on delete cascade,
 file_path text not null, file_type text not null, file_size bigint not null check(file_size>0),
 processing_status text not null default 'uploaded' check(processing_status in ('uploaded','processing','completed','failed')),
 created_at timestamptz not null default now(), unique(user_id,file_path)
);
create table public.detections (
 id uuid primary key default gen_random_uuid(), upload_id uuid not null references public.uploads on delete cascade,
 frame_number integer check(frame_number is null or frame_number>=0), class_name text not null,
 confidence real not null check(confidence between 0 and 1), x1 real not null, y1 real not null,
 x2 real not null, y2 real not null, crop_path text, created_at timestamptz not null default now(),
 check(x2>=x1 and y2>=y1)
);
create table public.identified_products (
 id uuid primary key default gen_random_uuid(), detection_id uuid not null unique references public.detections on delete cascade,
 brand text, category text, model text, color text, description text,
 confidence real check(confidence is null or confidence between 0 and 1), created_at timestamptz not null default now()
);
create table public.product_matches (
 id uuid primary key default gen_random_uuid(),
 identified_product_id uuid not null references public.identified_products on delete cascade,
 product_id uuid not null references public.products on delete cascade,
 visual_similarity real check(visual_similarity is null or visual_similarity between 0 and 1),
 text_similarity real check(text_similarity is null or text_similarity between 0 and 1),
 brand_score real check(brand_score is null or brand_score between 0 and 1),
 category_score real check(category_score is null or category_score between 0 and 1),
 final_score real not null check(final_score between 0 and 1), ranking integer not null check(ranking>0),
 created_at timestamptz not null default now(), unique(identified_product_id,product_id)
);
create table public.saved_products (
 id uuid primary key default gen_random_uuid(), user_id uuid not null references auth.users on delete cascade,
 product_id uuid not null references public.products on delete cascade, created_at timestamptz not null default now(),
 unique(user_id,product_id)
);
create table public.price_alerts (
 id uuid primary key default gen_random_uuid(), user_id uuid not null references auth.users on delete cascade,
 product_id uuid not null references public.products on delete cascade, target_price numeric(12,2) not null check(target_price>=0),
 currency varchar(3) not null check(currency ~ '^[A-Z]{3}$'), is_active boolean not null default true,
 created_at timestamptz not null default now(), triggered_at timestamptz
);

create index product_images_product_idx on public.product_images(product_id);
create index product_embeddings_product_idx on public.product_embeddings(product_id);
create index retailer_products_product_idx on public.retailer_products(product_id);
create index retailer_products_retailer_idx on public.retailer_products(retailer_id);
create index price_history_offer_time_idx on public.price_history(retailer_product_id,recorded_at desc);
create index uploads_user_time_idx on public.uploads(user_id,created_at desc);
create index detections_upload_idx on public.detections(upload_id);
create index product_matches_rank_idx on public.product_matches(identified_product_id,ranking);
create index saved_products_user_idx on public.saved_products(user_id,created_at desc);
create index price_alerts_active_idx on public.price_alerts(user_id) where is_active;

create function public.set_updated_at() returns trigger language plpgsql set search_path='' as $$
begin new.updated_at=now(); return new; end; $$;
create trigger products_updated_at before update on public.products for each row execute function public.set_updated_at();
create trigger retailer_products_updated_at before update on public.retailer_products for each row execute function public.set_updated_at();

alter table public.products enable row level security;
alter table public.product_images enable row level security;
alter table public.product_embeddings enable row level security;
alter table public.retailers enable row level security;
alter table public.retailer_products enable row level security;
alter table public.price_history enable row level security;
alter table public.uploads enable row level security;
alter table public.detections enable row level security;
alter table public.identified_products enable row level security;
alter table public.product_matches enable row level security;
alter table public.saved_products enable row level security;
alter table public.price_alerts enable row level security;

create policy "Catalog products are readable" on public.products for select to anon,authenticated using(true);
create policy "Product images are readable" on public.product_images for select to anon,authenticated using(true);
create policy "Retailers are readable" on public.retailers for select to anon,authenticated using(true);
create policy "Retailer offers are readable" on public.retailer_products for select to anon,authenticated using(true);
create policy "Price history is readable" on public.price_history for select to anon,authenticated using(true);
create policy "Users manage own uploads" on public.uploads for all to authenticated using((select auth.uid())=user_id) with check((select auth.uid())=user_id);
create policy "Users manage own saved products" on public.saved_products for all to authenticated using((select auth.uid())=user_id) with check((select auth.uid())=user_id);
create policy "Users manage own price alerts" on public.price_alerts for all to authenticated using((select auth.uid())=user_id) with check((select auth.uid())=user_id);
-- Processing outputs and embeddings remain inaccessible to client roles.

insert into storage.buckets(id,name,public,file_size_limit) values
 ('uploads','uploads',false,52428800),('product-images','product-images',true,10485760)
on conflict(id) do update set public=excluded.public,file_size_limit=excluded.file_size_limit;
create policy "Owners read uploaded objects" on storage.objects for select to authenticated
using(bucket_id='uploads' and (storage.foldername(name))[1]=(select auth.uid())::text);
create policy "Owners write uploaded objects" on storage.objects for insert to authenticated
with check(bucket_id='uploads' and (storage.foldername(name))[1]=(select auth.uid())::text);
create policy "Owners delete uploaded objects" on storage.objects for delete to authenticated
using(bucket_id='uploads' and (storage.foldername(name))[1]=(select auth.uid())::text);
create policy "Catalog images are public" on storage.objects for select to anon,authenticated using(bucket_id='product-images');

