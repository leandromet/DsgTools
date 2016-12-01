-- Database generated with pgModeler (PostgreSQL Database Modeler).
-- pgModeler  version: 0.8.0
-- PostgreSQL version: 9.3
-- Project Site: pgmodeler.com.br
-- Model Author: ---


-- Database creation must be done outside an multicommand file.
-- These commands were put in this file only for convenience.
-- -- object: dsgtools_admindb | type: DATABASE --
-- -- DROP DATABASE IF EXISTS dsgtools_admindb;
-- CREATE DATABASE dsgtools_admindb
-- ;
-- -- ddl-end --
-- 

-- object: topology | type: SCHEMA --
-- DROP SCHEMA IF EXISTS topology CASCADE;
CREATE SCHEMA topology;
-- ddl-end --
ALTER SCHEMA topology OWNER TO postgres;
-- ddl-end --

SET search_path TO pg_catalog,public,topology;
-- ddl-end --

-- object: postgis | type: EXTENSION --
-- DROP EXTENSION IF EXISTS postgis CASCADE;
CREATE EXTENSION postgis
      WITH SCHEMA public;
-- ddl-end --

-- object: postgis_topology | type: EXTENSION --
-- DROP EXTENSION IF EXISTS postgis_topology CASCADE;
CREATE EXTENSION postgis_topology
      WITH SCHEMA topology;
-- ddl-end --

-- object: "uuid-ossp" | type: EXTENSION --
-- DROP EXTENSION IF EXISTS "uuid-ossp" CASCADE;
CREATE EXTENSION "uuid-ossp"
      WITH SCHEMA public;
-- ddl-end --

-- object: public.permission_profile | type: TABLE --
-- DROP TABLE IF EXISTS public.permission_profile CASCADE;
CREATE TABLE public.permission_profile(
	id uuid NOT NULL DEFAULT uuid_generate_v4(),
	name text,
	jsondict text NOT NULL,
	edgvversion text,
	CONSTRAINT permissions_pk PRIMARY KEY (id),
	CONSTRAINT unique_name_and_version UNIQUE (name,edgvversion)

);
-- ddl-end --
ALTER TABLE public.permission_profile OWNER TO postgres;
-- ddl-end --

-- object: public.product | type: TABLE --
-- DROP TABLE IF EXISTS public.product CASCADE;
CREATE TABLE public.product(
	id uuid NOT NULL DEFAULT uuid_generate_v4(),
	inom text NOT NULL,
	mi smallint NOT NULL,
	dboid oid,
	CONSTRAINT product_pk PRIMARY KEY (id)

);
-- ddl-end --
ALTER TABLE public.product OWNER TO postgres;
-- ddl-end --

-- object: public.metadata | type: TABLE --
-- DROP TABLE IF EXISTS public.metadata CASCADE;
CREATE TABLE public.metadata(
	admindbversion text
);
-- ddl-end --
ALTER TABLE public.metadata OWNER TO postgres;
-- ddl-end --

-- object: public.admin_log | type: TABLE --
-- DROP TABLE IF EXISTS public.admin_log CASCADE;
CREATE TABLE public.admin_log(
	id serial NOT NULL,
	logtext text,
	time timestamp DEFAULT now(),
	CONSTRAINT admin_log_pk PRIMARY KEY (id)

);
-- ddl-end --
ALTER TABLE public.admin_log OWNER TO postgres;
-- ddl-end --

