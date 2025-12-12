-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.client (
  id integer GENERATED ALWAYS AS IDENTITY NOT NULL,
  company_id integer,
  name character varying NOT NULL,
  email character varying NOT NULL UNIQUE,
  address character varying NOT NULL,
  location character varying,
  CONSTRAINT client_pkey PRIMARY KEY (id),
  CONSTRAINT client_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.company(id)
);
CREATE TABLE public.company (
  id integer GENERATED ALWAYS AS IDENTITY NOT NULL,
  name character varying NOT NULL UNIQUE,
  email character varying,
  CONSTRAINT company_pkey PRIMARY KEY (id)
);
CREATE TABLE public.ground (
  id integer GENERATED ALWAYS AS IDENTITY NOT NULL,
  location character varying NOT NULL,
  m2 integer NOT NULL CHECK (m2 >= 0),
  budget numeric NOT NULL CHECK (budget >= 0::numeric),
  subdivision_type character varying NOT NULL,
  owner character varying NOT NULL,
  image_url text,
  address character varying,
  provider character varying,
  CONSTRAINT ground_pkey PRIMARY KEY (id)
);
CREATE TABLE public.match (
  id integer GENERATED ALWAYS AS IDENTITY NOT NULL,
  ground_id integer NOT NULL,
  m2_score numeric NOT NULL DEFAULT 0 CHECK (m2_score >= 0::numeric),
  budget_score numeric NOT NULL DEFAULT 0 CHECK (budget_score >= 0::numeric),
  status USER-DEFINED NOT NULL DEFAULT 'pending'::match_status,
  location_score numeric NOT NULL DEFAULT 0 CHECK (location_score >= 0::numeric),
  client_id integer NOT NULL,
  type_score numeric DEFAULT 0,
  CONSTRAINT match_pkey PRIMARY KEY (id),
  CONSTRAINT match_ground_id_fkey FOREIGN KEY (ground_id) REFERENCES public.ground(id),
  CONSTRAINT match_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.client(id)
);
CREATE TABLE public.preferences (
  id integer GENERATED ALWAYS AS IDENTITY NOT NULL,
  client_id integer NOT NULL,
  location character varying,
  subdivision_type character varying,
  min_m2 integer CHECK (min_m2 IS NULL OR min_m2 >= 0),
  max_m2 integer CHECK (max_m2 IS NULL OR max_m2 >= 0),
  min_budget numeric CHECK (min_budget IS NULL OR min_budget >= 0::numeric),
  max_budget numeric CHECK (max_budget IS NULL OR max_budget >= 0::numeric),
  CONSTRAINT preferences_pkey PRIMARY KEY (id),
  CONSTRAINT preferences_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.client(id)
);