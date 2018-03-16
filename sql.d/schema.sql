-- Copyright (C) 2016-2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
--
-- This file is part of repology
--
-- repology is free software: you can redistribute it and/or modify
-- it under the terms of the GNU General Public License as published by
-- the Free Software Foundation, either version 3 of the License, or
-- (at your option) any later version.
--
-- repology is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU General Public License for more details.
--
-- You should have received a copy of the GNU General Public License
-- along with repology.  If not, see <http://www.gnu.org/licenses/>.

--------------------------------------------------------------------------------
--
-- !!create_schema()
--
--------------------------------------------------------------------------------

--------------------------------------------------------------------------------
-- DROPs
--------------------------------------------------------------------------------
DROP TABLE IF EXISTS packages CASCADE;
DROP TABLE IF EXISTS repositories CASCADE;
DROP TABLE IF EXISTS repositories_history CASCADE;
DROP TABLE IF EXISTS statistics CASCADE;
DROP TABLE IF EXISTS statistics_history CASCADE;
DROP TABLE IF EXISTS links CASCADE;
DROP TABLE IF EXISTS problems CASCADE;
DROP TABLE IF EXISTS reports CASCADE;
DROP TABLE IF EXISTS metapackages CASCADE;
DROP TABLE IF EXISTS maintainers CASCADE;
DROP TABLE IF EXISTS metapackages_state CASCADE;
DROP TABLE IF EXISTS metapackages_events CASCADE;

DROP TYPE IF EXISTS metapackage_event_type CASCADE;

--------------------------------------------------------------------------------
-- types
--------------------------------------------------------------------------------

CREATE TYPE metapackage_event_type AS enum(
	'history_start',
	'repos_update',
	'version_update',
	'catch_up'
);

--------------------------------------------------------------------------------
-- functions
--------------------------------------------------------------------------------

-- Simplifies given url so https://www.foo.com and foo.com are the same
-- - Removes schema
-- - Removes www
-- - Removes parameters
-- XXX: should lowercase as well?
CREATE OR REPLACE FUNCTION simplify_url(url text) RETURNS text AS $$
BEGIN
	RETURN regexp_replace(regexp_replace(url, '/?([#?].*)?$', ''), '^https?://(www\.)?', '');
END;
$$ LANGUAGE plpgsql IMMUTABLE RETURNS NULL ON NULL INPUT;

-- Creates events on metapackage version state changes
CREATE OR REPLACE FUNCTION metapackage_create_events() RETURNS trigger AS $metapackage_create_events$
DECLARE
	catch_up text[];
	repos_added text[];
	repos_removed text[];
BEGIN
	IF (TG_OP = 'INSERT') THEN
		INSERT INTO metapackages_events (
			effname,
			ts,
			type,
			data
		) SELECT
			NEW.effname,
			now(),
			'history_start',
			jsonb_build_object(
				'newest_versions', NEW.newest_versions,
				'devel_versions', NEW.devel_versions,
				'unique_versions', NEW.unique_versions,
				'actual_repos', NEW.actual_repos,
				'all_repos', NEW.all_repos
			);

		RETURN NULL;
	END IF;

	IF (OLD.all_repos != NEW.all_repos) THEN
		repos_added := (SELECT array(SELECT unnest(NEW.all_repos) EXCEPT SELECT unnest(OLD.all_repos)));
		repos_removed := (SELECT array(SELECT unnest(OLD.all_repos) EXCEPT SELECT unnest(NEW.all_repos)));
		INSERT INTO metapackages_events (
			effname,
			ts,
			type,
			data
		) SELECT
			NEW.effname,
			now(),
			'repos_update',
			jsonb_build_object(
				'repos_added', repos_added,
				'repos_removed', repos_removed
			);
	END IF;

	catch_up := (SELECT array(SELECT unnest(NEW.actual_repos) EXCEPT SELECT unnest(OLD.actual_repos)));

	IF (OLD.newest_versions != NEW.newest_versions OR OLD.devel_versions != NEW.devel_versions OR OLD.unique_versions != NEW.unique_versions) THEN
		INSERT INTO metapackages_events (
			effname,
			ts,
			type,
			data
		) SELECT
			NEW.effname,
			now(),
			'version_update',
			jsonb_strip_nulls(jsonb_build_object(
				'newest_versions', NEW.newest_versions,
				'devel_versions', NEW.devel_versions,
				'unique_versions', NEW.unique_versions,
				'actual_repos', NEW.actual_repos,
				'since_previous', extract(epoch FROM now() - OLD.last_version_update)
			));
	ELSIF (catch_up != '{}') THEN
		INSERT INTO metapackages_events (
			effname,
			ts,
			type,
			data
		) SELECT
			NEW.effname,
			now(),
			'catch_up',
			jsonb_strip_nulls(jsonb_build_object(
				'repos', catch_up,
				'lag', extract(epoch FROM now() - OLD.last_version_update)
			));
	END IF;

	RETURN NULL;
END;
$metapackage_create_events$ LANGUAGE plpgsql;

--------------------------------------------------------------------------------
-- Main packages table
--------------------------------------------------------------------------------
CREATE TABLE packages (
	repo text NOT NULL,
	family text NOT NULL,
	subrepo text,

	name text NOT NULL,
	effname text NOT NULL,

	version text NOT NULL,
	origversion text,
	versionclass smallint,

	maintainers text[],
	category text,
	comment text,
	homepage text,
	licenses text[],
	downloads text[],

	flags smallint NOT NULL,
	shadow bool NOT NULL,
	verfixed bool NOT NULL,

	flavors text[],

	extrafields jsonb NOT NULL
);

CREATE INDEX ON packages(effname);

--------------------------------------------------------------------------------
-- Metapackages
--------------------------------------------------------------------------------
CREATE TABLE metapackages (
	effname text NOT NULL PRIMARY KEY,
	num_repos smallint NOT NULL,
	num_repos_nonshadow smallint NOT NULL,
	num_families smallint NOT NULL,
	num_repos_newest smallint NOT NULL,
	num_families_newest smallint NOT NULL,
	has_related boolean NOT NULL DEFAULT false,
	first_seen timestamp with time zone NOT NULL,
	last_seen timestamp with time zone NOT NULL
);

-- indexes for metapackage queries
CREATE UNIQUE INDEX metapackages_active_idx ON metapackages(effname) WHERE (num_repos_nonshadow > 0);
CREATE INDEX ON metapackages(num_repos) WHERE (num_repos_nonshadow > 0);
CREATE INDEX ON metapackages(num_families) WHERE (num_repos_nonshadow > 0);
CREATE INDEX metapackages_effname_trgm ON metapackages USING gin (effname gin_trgm_ops) WHERE (num_repos_nonshadow > 0);

-- index for recently_added
CREATE INDEX metapackages_recently_added_idx ON metapackages(first_seen DESC, effname) WHERE (num_repos_nonshadow > 0);

-- index for recently_removed
CREATE INDEX metapackages_recently_removed_idx ON metapackages(last_seen DESC, effname) WHERE (num_repos = 0);

--------------------------------------------------------------------------------
-- Metapackages state and events
--------------------------------------------------------------------------------
CREATE TABLE metapackages_state (
	effname text NOT NULL PRIMARY KEY,
	newest_versions text[],
	devel_versions text[],
	unique_versions text[],
	last_version_update timestamp with time zone,
	actual_repos text[],
	all_repos text[]
);

CREATE TABLE metapackages_events (
	effname text NOT NULL,
	ts timestamp with time zone NOT NULL,
	type metapackage_event_type NOT NULL,
	data jsonb NOT NULL
);

CREATE INDEX ON metapackages_events(effname, ts DESC, type DESC);

CREATE TRIGGER metapackages_state_create
	AFTER INSERT ON metapackages_state
	FOR EACH ROW
EXECUTE PROCEDURE metapackage_create_events();

CREATE TRIGGER metapackages_state_update
	AFTER UPDATE ON metapackages_state
	FOR EACH ROW WHEN (OLD.* IS DISTINCT FROM NEW.*)
EXECUTE PROCEDURE metapackage_create_events();

--------------------------------------------------------------------------------
-- Metapackages by repo/category/maintainer
--------------------------------------------------------------------------------

-- per-repository
CREATE MATERIALIZED VIEW repo_metapackages AS
SELECT
	repo,
	effname,
	count(*)::smallint AS num_packages,
	count(*) FILTER (WHERE versionclass = 1)::smallint AS num_packages_newest,
	count(*) FILTER (WHERE versionclass = 2)::smallint AS num_packages_outdated,
	count(*) FILTER (WHERE versionclass = 3)::smallint AS num_packages_ignored,
	count(*) FILTER (WHERE versionclass = 4)::smallint AS num_packages_unique,
	count(*) FILTER (WHERE versionclass = 5)::smallint AS num_packages_devel,
	count(*) FILTER (WHERE versionclass = 6)::smallint AS num_packages_legacy,
	count(*) FILTER (WHERE versionclass = 7)::smallint AS num_packages_incorrect,
	count(*) FILTER (WHERE versionclass = 8)::smallint AS num_packages_untrusted,
	count(*) FILTER (WHERE versionclass = 9)::smallint AS num_packages_noscheme,
	count(*) FILTER (WHERE versionclass = 10)::smallint AS num_packages_rolling,
	max(num_families) = 1 AS unique
FROM packages INNER JOIN metapackages USING(effname)
WHERE num_repos_nonshadow > 0
GROUP BY effname,repo
WITH DATA;

CREATE UNIQUE INDEX ON repo_metapackages(repo, effname);
CREATE INDEX ON repo_metapackages(effname);

-- per-category
CREATE MATERIALIZED VIEW category_metapackages AS
SELECT
	category,
	effname,
	max(num_families) = 1 AS unique
FROM packages INNER JOIN metapackages USING(effname)
WHERE num_repos_nonshadow > 0
GROUP BY effname,category
WITH DATA;

CREATE UNIQUE INDEX ON category_metapackages(category, effname);
CREATE INDEX ON category_metapackages(effname);

-- per-maintainer
CREATE MATERIALIZED VIEW maintainer_metapackages AS
SELECT
	unnest(maintainers) AS maintainer,
	effname,
	count(1)::smallint AS num_packages,
	count(*) FILTER (WHERE versionclass = 1)::smallint AS num_packages_newest,
	count(*) FILTER (WHERE versionclass = 2)::smallint AS num_packages_outdated,
	count(*) FILTER (WHERE versionclass = 3)::smallint AS num_packages_ignored,
	count(*) FILTER (WHERE versionclass = 4)::smallint AS num_packages_unique,
	count(*) FILTER (WHERE versionclass = 5)::smallint AS num_packages_devel,
	count(*) FILTER (WHERE versionclass = 6)::smallint AS num_packages_legacy,
	count(*) FILTER (WHERE versionclass = 7)::smallint AS num_packages_incorrect,
	count(*) FILTER (WHERE versionclass = 8)::smallint AS num_packages_untrusted,
	count(*) FILTER (WHERE versionclass = 9)::smallint AS num_packages_noscheme,
	count(*) FILTER (WHERE versionclass = 10)::smallint AS num_packages_rolling
FROM packages
GROUP BY maintainer, effname
WITH DATA;

CREATE UNIQUE INDEX ON maintainer_metapackages(maintainer, effname);
CREATE INDEX ON maintainer_metapackages(effname);

--------------------------------------------------------------------------------
-- Maintainers
--------------------------------------------------------------------------------

CREATE TABLE maintainers (
	maintainer text NOT NULL PRIMARY KEY,
	num_packages integer NOT NULL,
	num_packages_newest integer NOT NULL,
	num_packages_outdated integer NOT NULL,
	num_packages_ignored integer NOT NULL,
	num_packages_unique integer NOT NULL,
	num_packages_devel integer NOT NULL,
	num_packages_legacy integer NOT NULL,
	num_packages_incorrect integer NOT NULL,
	num_packages_untrusted integer NOT NULL,
	num_packages_noscheme integer NOT NULL,
	num_packages_rolling integer NOT NULL,
	num_metapackages integer NOT NULL,
	num_metapackages_outdated integer NOT NULL,
	repository_package_counts jsonb NOT NULL DEFAULT '{}',
	repository_metapackage_counts jsonb NOT NULL DEFAULT '{}',
	category_metapackage_counts jsonb NOT NULL DEFAULT '{}',
	first_seen timestamp with time zone NOT NULL,
	last_seen timestamp with time zone NOT NULL
);

-- indexes for maintainer queries
CREATE UNIQUE INDEX maintainers_active_idx ON maintainers(maintainer) WHERE (num_packages > 0);
CREATE INDEX maintainers_maintainer_trgm ON maintainers USING gin (maintainer gin_trgm_ops) WHERE (num_packages > 0);

-- index for recently_added
CREATE INDEX maintainers_recently_added_idx ON maintainers(first_seen DESC, maintainer) WHERE (num_packages > 0);

-- index for recently_removed
CREATE INDEX maintainers_recently_removed_idx ON maintainers(last_seen DESC, maintainer) WHERE (num_packages = 0);

--------------------------------------------------------------------------------
-- Per-repository and global statistics and their history
--------------------------------------------------------------------------------
CREATE TABLE repositories (
	name text NOT NULL PRIMARY KEY,

	num_packages integer NOT NULL DEFAULT 0,
	num_packages_newest integer NOT NULL DEFAULT 0,
	num_packages_outdated integer NOT NULL DEFAULT 0,
	num_packages_ignored integer NOT NULL DEFAULT 0,
	num_packages_unique integer NOT NULL DEFAULT 0,
	num_packages_devel integer NOT NULL DEFAULT 0,
	num_packages_legacy integer NOT NULL DEFAULT 0,
	num_packages_incorrect integer NOT NULL DEFAULT 0,
	num_packages_untrusted integer NOT NULL DEFAULT 0,
	num_packages_noscheme integer NOT NULL DEFAULT 0,
	num_packages_rolling integer NOT NULL DEFAULT 0,

	num_metapackages integer NOT NULL DEFAULT 0,
	num_metapackages_unique integer NOT NULL DEFAULT 0,
	num_metapackages_newest integer NOT NULL DEFAULT 0,
	num_metapackages_outdated integer NOT NULL DEFAULT 0,
	num_metapackages_comparable integer NOT NULL DEFAULT 0,

	last_update timestamp with time zone,

	num_problems integer NOT NULL DEFAULT 0,
	num_maintainers integer NOT NULL DEFAULT 0
);

-- repository_history
CREATE TABLE repositories_history (
	ts timestamp with time zone NOT NULL PRIMARY KEY,
	snapshot jsonb NOT NULL
);

-- statistics
CREATE TABLE statistics (
	num_packages integer NOT NULL DEFAULT 0,
	num_metapackages integer NOT NULL DEFAULT 0,
	num_problems integer NOT NULL DEFAULT 0,
	num_maintainers integer NOT NULL DEFAULT 0
);

INSERT INTO statistics VALUES(DEFAULT);

-- statistics_history
CREATE TABLE statistics_history (
	ts timestamp with time zone NOT NULL PRIMARY KEY,
	snapshot jsonb NOT NULL
);

--------------------------------------------------------------------------------
-- Links
--------------------------------------------------------------------------------
CREATE TABLE links (
	url text NOT NULL PRIMARY KEY,
	first_extracted timestamp with time zone NOT NULL,
	last_extracted timestamp with time zone NOT NULL,
	last_checked timestamp with time zone,
	last_success timestamp with time zone,
	last_failure timestamp with time zone,
	status smallint,
	redirect smallint,
	size bigint,
	location text
);

--------------------------------------------------------------------------------
-- Problems
--------------------------------------------------------------------------------
CREATE TABLE problems (
	repo text NOT NULL,
	name text NOT NULL,
	effname text NOT NULL,
	maintainer text,
	problem text NOT NULL
);

CREATE INDEX ON problems(effname);
CREATE INDEX ON problems(repo, effname);
CREATE INDEX ON problems(maintainer);

--------------------------------------------------------------------------------
-- Reports
--------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reports (
	id integer GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
	created timestamp with time zone NOT NULL,
	effname text NOT NULL,
	need_verignore boolean NOT NULL,
	need_split boolean NOT NULL,
	need_merge boolean NOT NULL,
	comment text,
	reply text,
	accepted boolean
);

CREATE INDEX ON reports(effname);

--------------------------------------------------------------------------------
-- Url relations
--------------------------------------------------------------------------------
CREATE MATERIALIZED VIEW url_relations AS
SELECT DISTINCT
	effname,
	simplify_url(homepage) AS url
FROM packages
WHERE homepage ~ '^https?://'
WITH DATA;

CREATE UNIQUE INDEX ON url_relations(effname, url);  -- we only need url here because we need unique index for concurrent refresh
CREATE INDEX ON url_relations(url);
