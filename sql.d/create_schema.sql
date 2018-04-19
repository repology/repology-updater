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
DROP TABLE IF EXISTS repo_metapackages CASCADE;
DROP TABLE IF EXISTS category_metapackages CASCADE;
DROP TABLE IF EXISTS maintainer_metapackages CASCADE;
DROP TABLE IF EXISTS url_relations CASCADE;

DROP TYPE IF EXISTS metapackage_event_type CASCADE;

DROP FUNCTION IF EXISTS simplify_url CASCADE;
DROP FUNCTION IF EXISTS version_set_changed CASCADE;
DROP FUNCTION IF EXISTS metapackage_create_event CASCADE;
DROP FUNCTION IF EXISTS metapackage_create_events_trigger CASCADE;

--------------------------------------------------------------------------------
-- types
--------------------------------------------------------------------------------

CREATE TYPE metapackage_event_type AS enum(
	'history_start',
	'repos_update',
	'version_update',
	'catch_up',
	'history_end'
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

-- Checks whether version set has effectively changed
CREATE OR REPLACE FUNCTION version_set_changed(old text[], new text[]) RETURNS bool AS $$
BEGIN
	RETURN
		(
			old IS NOT NULL AND
			new IS NOT NULL AND
			version_compare_simple(old[1], new[1]) != 0
		) OR (old IS NULL) != (new IS NULL);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Creates events on metapackage version state changes
CREATE OR REPLACE FUNCTION metapackage_create_event(effname text, type metapackage_event_type, data jsonb) RETURNS void AS $$
BEGIN
	INSERT INTO metapackages_events (
		effname,
		ts,
		type,
		data
	) SELECT
		effname,
		now(),
		type,
		jsonb_strip_nulls(data);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION metapackage_create_events_trigger() RETURNS trigger AS $$
DECLARE
	catch_up text[];
	repos_added text[];
	repos_removed text[];
BEGIN
	-- history_start
	IF (TG_OP = 'INSERT' OR OLD.all_repos IS NULL) THEN
		PERFORM metapackage_create_event(NEW.effname, 'history_start'::metapackage_event_type,
			jsonb_build_object(
				'devel_versions', NEW.devel_versions,
				'newest_versions', NEW.newest_versions,
				'devel_repos', NEW.devel_repos,
				'newest_repos', NEW.newest_repos,
				'all_repos', NEW.all_repos
			)
		);

		RETURN NULL;
	END IF;

	-- repos_update
	IF (OLD.all_repos != NEW.all_repos) THEN
		repos_added := (SELECT array(SELECT unnest(NEW.all_repos) EXCEPT SELECT unnest(OLD.all_repos)));
		repos_removed := (SELECT array(SELECT unnest(OLD.all_repos) EXCEPT SELECT unnest(NEW.all_repos)));

		PERFORM metapackage_create_event(NEW.effname, 'repos_update'::metapackage_event_type,
			jsonb_build_object(
				'repos_added', repos_added,
				'repos_removed', repos_removed
			)
		);
	END IF;

	-- version_update & catch_up for devel
	IF (version_set_changed(OLD.devel_versions, NEW.devel_versions)) THEN
		PERFORM metapackage_create_event(NEW.effname, 'version_update'::metapackage_event_type,
			jsonb_build_object(
				'branch', 'devel',
				'versions', NEW.devel_versions,
				'repos', NEW.devel_repos,
				'passed',
					CASE
						WHEN
							-- only account if the repository hasn't just appeared
							EXISTS (SELECT unnest(NEW.devel_repos) INTERSECT SELECT unnest(OLD.all_repos))
						THEN
							extract(epoch FROM now() - OLD.devel_version_update)
						ELSE NULL
					END
			)
		);
	ELSE
		catch_up := (SELECT array(SELECT unnest(NEW.devel_repos) EXCEPT SELECT unnest(OLD.devel_repos)));
		IF (catch_up != '{}') THEN
			PERFORM metapackage_create_event(NEW.effname, 'catch_up'::metapackage_event_type,
				jsonb_build_object(
					'branch', 'devel',
					'repos', catch_up,
					'lag',
						CASE
							WHEN
								-- only account if the repository hasn't just appeared
								EXISTS (SELECT unnest(NEW.devel_repos) INTERSECT SELECT unnest(OLD.all_repos))
							THEN
								extract(epoch FROM now() - OLD.devel_version_update)
							ELSE NULL
						END
				)
			);
		END IF;
	END IF;

	-- version_update & catch_up for newest
	IF (version_set_changed(OLD.newest_versions, NEW.newest_versions)) THEN
		PERFORM metapackage_create_event(NEW.effname, 'version_update'::metapackage_event_type,
			jsonb_build_object(
				'branch', 'newest',
				'versions', NEW.newest_versions,
				'repos', NEW.newest_repos,
				'passed',
					CASE
						WHEN
							-- only account if the repository hasn't just appeared
							EXISTS (SELECT unnest(NEW.newest_repos) INTERSECT SELECT unnest(OLD.all_repos))
						THEN
							extract(epoch FROM now() - OLD.newest_version_update)
						ELSE NULL
					END
			)
		);
	ELSE
		catch_up := (SELECT array(SELECT unnest(NEW.newest_repos) EXCEPT SELECT unnest(OLD.newest_repos)));
		IF (catch_up != '{}') THEN
			PERFORM metapackage_create_event(NEW.effname, 'catch_up'::metapackage_event_type,
				jsonb_build_object(
					'branch', 'newest',
					'repos', catch_up,
					'lag',
						CASE
							WHEN
								-- only account if the repository hasn't just appeared
								EXISTS (SELECT unnest(NEW.newest_repos) INTERSECT SELECT unnest(OLD.all_repos))
							THEN
								extract(epoch FROM now() - OLD.newest_version_update)
							ELSE NULL
						END
				)
			);
		END IF;
	END IF;

	-- history_end
	IF (NEW.num_repos = 0) THEN
		PERFORM metapackage_create_event(NEW.effname, 'history_end'::metapackage_event_type,
			jsonb_build_object(
				'last_repos', OLD.all_repos
			)
		);
	END IF;

	RETURN NULL;
END;
$$ LANGUAGE plpgsql;

--------------------------------------------------------------------------------
-- Main packages table
--------------------------------------------------------------------------------
CREATE TABLE packages (
	id integer GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
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
	id integer GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
	effname text NOT NULL,

	num_repos smallint NOT NULL,
	num_repos_nonshadow smallint NOT NULL,
	num_families smallint NOT NULL,
	num_repos_newest smallint NOT NULL,
	num_families_newest smallint NOT NULL,
	max_repos smallint NOT NULL,
	max_families smallint NOT NULL,
	has_related boolean NOT NULL DEFAULT false,
	first_seen timestamp with time zone NOT NULL,
	last_seen timestamp with time zone NOT NULL,

	devel_versions text[],
	devel_repos text[],
	devel_version_update timestamp with time zone,

	newest_versions text[],
	newest_repos text[],
	newest_version_update timestamp with time zone,

	all_repos text[]
);

-- indexes for metapackage queries
CREATE UNIQUE INDEX ON metapackages(effname);
CREATE UNIQUE INDEX metapackages_active_idx ON metapackages(effname) WHERE (num_repos_nonshadow > 0);
CREATE INDEX metapackages_effname_trgm ON metapackages USING gin (effname gin_trgm_ops) WHERE (num_repos_nonshadow > 0);
-- note that the following indexes exclude the most selective values - scan by metapackages_active_idx will be faster for these values anyway
CREATE INDEX ON metapackages(num_repos) WHERE (num_repos_nonshadow > 0 AND num_repos >= 5);
CREATE INDEX ON metapackages(num_families) WHERE (num_repos_nonshadow > 0 AND num_families >= 5);
CREATE INDEX ON metapackages(num_repos_newest) WHERE (num_repos_nonshadow > 0 AND num_repos_newest >= 1);
CREATE INDEX ON metapackages(num_families_newest) WHERE (num_repos_nonshadow > 0 AND num_families_newest >= 1);

-- index for recently_added
CREATE INDEX metapackages_recently_added_idx ON metapackages(first_seen DESC, effname) WHERE (num_repos_nonshadow > 0);

-- index for recently_removed
CREATE INDEX metapackages_recently_removed_idx ON metapackages(last_seen DESC, effname) WHERE (num_repos = 0);

-- events
CREATE TABLE metapackages_events (
	effname text NOT NULL,
	ts timestamp with time zone NOT NULL,
	type metapackage_event_type NOT NULL,
	data jsonb NOT NULL
);

CREATE INDEX ON metapackages_events(effname, ts DESC, type DESC);

-- triggers
CREATE TRIGGER metapackage_create
	AFTER INSERT ON metapackages
	FOR EACH ROW
EXECUTE PROCEDURE metapackage_create_events_trigger();

CREATE TRIGGER metapackage_update
	AFTER UPDATE ON metapackages
	FOR EACH ROW WHEN (OLD.* IS DISTINCT FROM NEW.*)
EXECUTE PROCEDURE metapackage_create_events_trigger();

--------------------------------------------------------------------------------
-- Maintainers
--------------------------------------------------------------------------------
CREATE TABLE maintainers (
	id integer GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
	maintainer text NOT NULL,

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
CREATE UNIQUE INDEX ON maintainers(maintainer);
CREATE UNIQUE INDEX maintainers_active_idx ON maintainers(maintainer) WHERE (num_packages > 0);
CREATE INDEX maintainers_maintainer_trgm ON maintainers USING gin (maintainer gin_trgm_ops) WHERE (num_packages > 0);

-- index for recently_added
CREATE INDEX maintainers_recently_added_idx ON maintainers(first_seen DESC, maintainer) WHERE (num_packages > 0);

-- index for recently_removed
CREATE INDEX maintainers_recently_removed_idx ON maintainers(last_seen DESC, maintainer) WHERE (num_packages = 0);

--------------------------------------------------------------------------------
-- Repositories
--------------------------------------------------------------------------------
CREATE TABLE repositories (
	id smallint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
	name text NOT NULL,

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
	num_maintainers integer NOT NULL DEFAULT 0,

	first_seen timestamp with time zone NOT NULL,
	last_seen timestamp with time zone NOT NULL
);

CREATE UNIQUE INDEX ON repositories(name);

-- history
CREATE TABLE repositories_history (
	ts timestamp with time zone NOT NULL PRIMARY KEY,
	snapshot jsonb NOT NULL
);

--------------------------------------------------------------------------------
-- Tables binding metapackages and other entities
--------------------------------------------------------------------------------

-- per-repository
CREATE TABLE repo_metapackages (
	repository_id smallint NOT NULL,
	effname text NOT NULL,

	newest boolean NOT NULL,
	outdated boolean NOT NULL,
	problematic boolean NOT NULL,
	"unique" boolean NOT NULL,

	PRIMARY KEY(repository_id, effname)
);

CREATE INDEX ON repo_metapackages(effname);

-- per-category
CREATE TABLE category_metapackages (
	category text NOT NULL,
	effname text NOT NULL,
	"unique" boolean NOT NULL,

	PRIMARY KEY(category, effname)
);

CREATE INDEX ON category_metapackages(effname);

-- per-maintainer
CREATE TABLE maintainer_metapackages (
	maintainer_id integer NOT NULL,
	effname text NOT NULL,

	newest boolean NOT NULL,
	outdated boolean NOT NULL,
	problematic boolean NOT NULL,
	PRIMARY KEY(maintainer_id, effname)
);

CREATE INDEX ON maintainer_metapackages(effname);

--------------------------------------------------------------------------------
-- Statistics
--------------------------------------------------------------------------------
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
	package_id integer NOT NULL,
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
	client text,
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
CREATE TABLE url_relations (
	effname text NOT NULL,
	url text NOT NULL,
	PRIMARY KEY(effname, url)
);

CREATE INDEX ON url_relations(url, effname);
