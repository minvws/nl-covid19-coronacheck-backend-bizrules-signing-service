-- Datum : 20-04-2021
-- Waarom : Setup vcbe_db users
-- Wie   : Rob


do $$
<<first_block>>
declare
  ln_count integer := 0;
begin
   -- Check if user exists

   select count(*)
   into ln_count
   from pg_user
   where usename = 'minous';

   if ln_count = 0 then
     CREATE user minous password 'minous';
   end if;

   select count(*)
   into ln_count
   from pg_user
   where usename = 'vcbe_dba';

   if ln_count = 0 then
     CREATE user vcbe_dba password 'vcbe_dba';
   end if;

   select count(*)
   into ln_count
   from pg_user
   where usename = 'cims_ro';

   if ln_count = 0 then
     CREATE user cims_or password 'cims_ro';
   end if;

end first_block $$;
-- Datum : 20-04-2021
-- Waarom : Setup vcbe_db users
-- Wie   : Rob

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


GRANT CONNECT ON DATABASE vcbe_db to minous;
GRANT CONNECT ON DATABASE vcbe_db to cims_ro;


-- Datum : 20-04-2021
-- Waarom : Setup vcbe_db users
-- Wie   : Rob

CREATE TABLE public.vaccinatie_event (
  id bigint  NOT NULL,
  bsn_external varchar(64) NOT NULL,
  bsn_internal varchar(64) NOT NULL,
  payload varchar(2048) NOT NULL,
  version_cims varchar(10) NOT NULL,
  version_vcbe varchar(10) not null,
  created_at   timestamp(0) default current_timestamp
);

ALTER TABLE ONLY public.vaccinatie_event
    ADD CONSTRAINT vaccinatie_event_pkey PRIMARY KEY (id);


ALTER TABLE public.vaccinatie_event OWNER TO vcbe_dba;

-- Make sure the user only can add and read. Deletion and updating could change the integrity of the data
REVOKE ALL ON TABLE public.vaccinatie_event FROM cims_ro;
GRANT SELECT ON TABLE public.vaccinatie_event TO minous;

CREATE INDEX idx_vaccinatie_event_bsn_external ON public.vaccinatie_event (bsn_external);
CREATE INDEX idx_vaccinatie_event_bsn_internal ON public.vaccinatie_event (bsn_internal);
-- Datum : 20-04-2021
-- Waarom : Setup vcbe_db users
-- Wie   : Rob

CREATE TABLE public.vaccinatie_event_info (
  datetime_refresh timestamp(0) not null,
  duration_refresh integer not null,
  refresh_type varchar(1) not null,
  result  varchar(1) not null
);

ALTER TABLE public.vaccinatie_event_info OWNER TO vcbe_dba;


-- Datum : 20-04-2021
-- Waarom : Setup vcbe_db users
-- Wie   : Rob

CREATE TABLE public.vaccinatie_event_logging (
  created_date date not null,
  bsn_external varchar(64) not null,
  channel varchar(10) not null default 'cims',
  created_at timestamp(0) not null
) PARTITION BY RANGE (created_date);

ALTER TABLE public.vaccinatie_event_logging OWNER TO vcbe_dba;

CREATE TABLE vaccinatie_event_logging_20210420 PARTITION OF vaccinatie_event_logging
    FOR VALUES FROM ('2021-04-20') TO ('2021-04-21');

CREATE TABLE vaccinatie_event_logging_20210421 PARTITION OF vaccinatie_event_logging
    FOR VALUES FROM ('2021-04-21') TO ('2021-04-22');

CREATE TABLE vaccinatie_event_logging_20210422 PARTITION OF vaccinatie_event_logging
    FOR VALUES FROM ('2021-04-22') TO ('2021-04-23');

CREATE TABLE vaccinatie_event_logging_20210423 PARTITION OF vaccinatie_event_logging
    FOR VALUES FROM ('2021-04-23') TO ('2021-04-24');

CREATE TABLE vaccinatie_event_logging_20210424 PARTITION OF vaccinatie_event_logging
    FOR VALUES FROM ('2021-04-24') TO ('2021-04-25');

CREATE TABLE vaccinatie_event_logging_20210425 PARTITION OF vaccinatie_event_logging
    FOR VALUES FROM ('2021-04-25') TO ('2021-04-26');

CREATE TABLE vaccinatie_event_logging_20210426 PARTITION OF vaccinatie_event_logging
    FOR VALUES FROM ('2021-04-26') TO ('2021-04-27');

ALTER TABLE public.vaccinatie_event_logging OWNER TO vcbe_dba;

REVOKE ALL ON TABLE public.vaccinatie_event_logging FROM cims_ro;
GRANT INSERT, SELECT ON TABLE public.vaccinatie_event_logging TO minous;
GRANT SELECT ON TABLE public.vaccinatie_event_logging TO cims_ro;


-- Datum : 20-04-2021
-- Waarom : Setup vcbe_db users
-- Wie   : Rob

CREATE TABLE public.vaccinatie_event_request (
  created_date date not null,
  bsn_external varchar(64) not null,
  channel varchar(10) not null default 'cims',
  created_at timestamp(0) not null
) PARTITION BY RANGE (created_date);

ALTER TABLE public.vaccinatie_event_request OWNER TO vcbe_dba;

CREATE TABLE vaccinatie_event_request_20210420 PARTITION OF vaccinatie_event_request
    FOR VALUES FROM ('2021-04-20') TO ('2021-04-21');

CREATE TABLE vaccinatie_event_request_20210421 PARTITION OF vaccinatie_event_request
    FOR VALUES FROM ('2021-04-21') TO ('2021-04-22');

CREATE TABLE vaccinatie_event_request_20210422 PARTITION OF vaccinatie_event_request
    FOR VALUES FROM ('2021-04-22') TO ('2021-04-23');

CREATE TABLE vaccinatie_event_request_20210423 PARTITION OF vaccinatie_event_request
    FOR VALUES FROM ('2021-04-23') TO ('2021-04-24');

CREATE TABLE vaccinatie_event_request_20210424 PARTITION OF vaccinatie_event_request
    FOR VALUES FROM ('2021-04-24') TO ('2021-04-25');

CREATE TABLE vaccinatie_event_request_20210425 PARTITION OF vaccinatie_event_request
    FOR VALUES FROM ('2021-04-25') TO ('2021-04-26');

CREATE TABLE vaccinatie_event_request_20210426 PARTITION OF vaccinatie_event_request
    FOR VALUES FROM ('2021-04-26') TO ('2021-04-27');

ALTER TABLE public.vaccinatie_event_logging OWNER TO vcbe_dba;

REVOKE ALL ON TABLE public.vaccinatie_event_request FROM cims_ro;
GRANT INSERT, SELECT ON TABLE public.vaccinatie_event_request TO minous;
GRANT SELECT ON TABLE public.vaccinatie_event_request TO cims_ro;


