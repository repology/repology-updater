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
-- types
--------------------------------------------------------------------------------

DROP TYPE IF EXISTS metapackage_event_type CASCADE;

CREATE TYPE metapackage_event_type AS enum(
	'history_start',
	'repos_update',
	'version_update',
	'catch_up',
	'history_end'
);

DROP TYPE IF EXISTS maintainer_repo_metapackages_event_type CASCADE;

CREATE TYPE maintainer_repo_metapackages_event_type AS enum(
	'added',
	'uptodate',
	'outdated',
	'ignored',
	'removed'
);

DROP TYPE IF EXISTS repository_state CASCADE;

CREATE TYPE repository_state AS enum(
	'new',
	'active',
	'legacy'
);

DROP TYPE IF EXISTS run_type CASCADE;

CREATE TYPE run_type AS enum(
	'fetch',
	'parse',
	'database_push',
	'database_postprocess'
);

DROP TYPE IF EXISTS run_status CASCADE;

CREATE TYPE run_status AS enum(
	'running',
	'successful',
	'failed',
	'interrupted'
);

DROP TYPE IF EXISTS log_severity CASCADE;

CREATE TYPE log_severity AS enum(
	'notice',
	'warning',
	'error'
);

--------------------------------------------------------------------------------
-- functions
--------------------------------------------------------------------------------

-- Simplifies given url so https://www.foo.com and foo.com are the same
-- - Removes schema
-- - Removes www
-- - Removes parameters
-- XXX: should lowercase as well?
DROP FUNCTION IF EXISTS simplify_url CASCADE;

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

-- Returns repositories which should be added to oldrepos to get newrepos and filters active ones
CREATE OR REPLACE FUNCTION get_added_active_repos(oldrepos text[], newrepos text[]) RETURNS text[] AS $$
BEGIN
	RETURN array((SELECT unnest(newrepos) EXCEPT SELECT unnest(oldrepos)) INTERSECT SELECT name FROM repositories WHERE state = 'active');
END;
$$ LANGUAGE plpgsql IMMUTABLE RETURNS NULL ON NULL INPUT;

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
	repos_added := (SELECT get_added_active_repos(OLD.all_repos, NEW.all_repos));
	repos_removed := (SELECT get_added_active_repos(NEW.all_repos, OLD.all_repos));
	IF (repos_added != repos_removed) THEN
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
		catch_up := (SELECT get_added_active_repos(OLD.devel_repos, NEW.devel_repos));
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
		catch_up := (SELECT get_added_active_repos(OLD.newest_repos, NEW.newest_repos));
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

CREATE OR REPLACE FUNCTION maintainer_repo_metapackages_create_event(maintainer_id integer, repository_id smallint, metapackage_id integer, type maintainer_repo_metapackages_event_type, data jsonb) RETURNS void AS $$
BEGIN
	INSERT INTO maintainer_repo_metapackages_events (
		maintainer_id,
		repository_id,
		ts,
		metapackage_id,
		type,
		data
	) SELECT
		maintainer_id,
		repository_id,
		now(),
		metapackage_id,
		type,
		jsonb_strip_nulls(data);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION maintainer_repo_metapackages_create_events_trigger() RETURNS trigger AS $$
BEGIN
	-- remove
	IF (TG_OP = 'DELETE') THEN
		IF (EXISTS (SELECT * FROM repositories WHERE id = OLD.repository_id AND state = 'active'::repository_state)) THEN
			PERFORM maintainer_repo_metapackages_create_event(OLD.maintainer_id, OLD.repository_id, OLD.metapackage_id, 'removed'::maintainer_repo_metapackages_event_type, '{}'::jsonb);
		END IF;
		RETURN NULL;
	END IF;

	IF (NOT EXISTS (SELECT * FROM repositories WHERE id = NEW.repository_id AND state = 'active'::repository_state)) THEN
		RETURN NULL;
	END IF;

	-- add
	IF (TG_OP = 'INSERT') THEN
		PERFORM maintainer_repo_metapackages_create_event(NEW."maintainer_id", NEW.repository_id, NEW.metapackage_id, 'added'::maintainer_repo_metapackages_event_type, '{}'::jsonb);
	END IF;

	-- update
	IF (NEW.versions_uptodate IS NOT NULL AND (TG_OP = 'INSERT' OR OLD.versions_uptodate[1] IS DISTINCT FROM NEW.versions_uptodate[1])) THEN
		PERFORM maintainer_repo_metapackages_create_event(NEW.maintainer_id, NEW.repository_id, NEW.metapackage_id, 'uptodate'::maintainer_repo_metapackages_event_type,
			jsonb_build_object('version', NEW.versions_uptodate[1])
		);
	END IF;

	IF (NEW.versions_outdated IS NOT NULL AND (TG_OP = 'INSERT' OR OLD.versions_outdated[1] IS DISTINCT FROM NEW.versions_outdated[1])) THEN
		PERFORM maintainer_repo_metapackages_create_event(NEW.maintainer_id, NEW.repository_id, NEW.metapackage_id, 'outdated'::maintainer_repo_metapackages_event_type,
			jsonb_build_object(
				'version', NEW.versions_outdated[1],
				'newest_versions', (SELECT devel_versions||newest_versions FROM metapackages WHERE id = NEW.metapackage_id)
			)
		);
	END IF;

	IF (NEW.versions_ignored IS NOT NULL AND (TG_OP = 'INSERT' OR OLD.versions_ignored[1] IS DISTINCT FROM NEW.versions_ignored[1])) THEN
		PERFORM maintainer_repo_metapackages_create_event(NEW.maintainer_id, NEW.repository_id, NEW.metapackage_id, 'ignored'::maintainer_repo_metapackages_event_type,
			jsonb_build_object('version', NEW.versions_ignored[1])
		);
	END IF;

	RETURN NULL;
END;
$$ LANGUAGE plpgsql;

--------------------------------------------------------------------------------
-- Main packages table
--------------------------------------------------------------------------------
DROP TABLE IF EXISTS packages CASCADE;

CREATE TABLE packages (
	id integer GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,

	-- parsed, immutable
	repo text NOT NULL,
	family text NOT NULL,
	subrepo text,

	name text NOT NULL,
	basename text NULL,

	origversion text NOT NULL,
	rawversion text NOT NULL,

	arch text,

	maintainers text[],
	category text,
	comment text,
	homepage text,
	licenses text[],
	downloads text[],

	extrafields jsonb NOT NULL,

	-- calculated
	effname text NOT NULL,
	version text NOT NULL,
	versionclass smallint,

	flags smallint NOT NULL,
	shadow bool NOT NULL,

	flavors text[]
);

CREATE INDEX ON packages(effname);

--------------------------------------------------------------------------------
-- Metapackages
--------------------------------------------------------------------------------
DROP TABLE IF EXISTS metapackages CASCADE;

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
DROP TABLE IF EXISTS metapackages_events CASCADE;

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
	FOR EACH ROW WHEN (
		OLD.devel_versions IS DISTINCT FROM NEW.devel_versions OR
		OLD.devel_repos IS DISTINCT FROM NEW.devel_repos OR
		OLD.newest_versions IS DISTINCT FROM NEW.newest_versions OR
		OLD.newest_repos IS DISTINCT FROM NEW.newest_repos OR
		OLD.all_repos IS DISTINCT FROM NEW.all_repos OR
		NEW.num_repos = 0
	)
EXECUTE PROCEDURE metapackage_create_events_trigger();

--------------------------------------------------------------------------------
-- Maintainers
--------------------------------------------------------------------------------
DROP TABLE IF EXISTS maintainers CASCADE;

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
-- Runs and logs
--------------------------------------------------------------------------------
DROP TABLE IF EXISTS runs CASCADE;

CREATE TABLE runs (
	id integer GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,

	"type" run_type NOT NULL,
	repository_id smallint,

	status run_status NOT NULL DEFAULT 'running'::run_status,
	no_changes boolean NOT NULL DEFAULT false,

	start_ts timestamp with time zone NOT NULL,
	finish_ts timestamp with time zone NULL,

	num_lines integer NULL,
	num_warnings integer NULL,
	num_errors integer NULL,

	utime interval NULL,
	stime interval NULL,
	maxrss integer NULL,
	maxrss_delta integer NULL,

	traceback text NULL
);

CREATE INDEX runs_repository_id_start_ts_idx ON runs(repository_id, start_ts DESC);
CREATE INDEX runs_repository_id_start_ts_idx_failed ON runs(repository_id, start_ts DESC) WHERE(status = 'failed'::run_status);

DROP TABLE IF EXISTS log_lines CASCADE;

CREATE TABLE log_lines (
	run_id integer NOT NULL,
	lineno integer NOT NULL,

	timestamp timestamp with time zone NOT NULL,
	severity log_severity NOT NULL,
	message text NOT NULL,

	PRIMARY KEY(run_id, lineno, timestamp, severity)
);

--------------------------------------------------------------------------------
-- Repositories
--------------------------------------------------------------------------------
DROP TABLE IF EXISTS repositories CASCADE;

CREATE TABLE repositories (
	id smallint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
	name text NOT NULL,
	state repository_state NOT NULL,

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
	num_metapackages_problematic integer NOT NULL DEFAULT 0,

	num_problems integer NOT NULL DEFAULT 0,
	num_maintainers integer NOT NULL DEFAULT 0,

	first_seen timestamp with time zone NOT NULL,
	last_seen timestamp with time zone NOT NULL,

	-- metadata
	sortname text NOT NULL,
	"type" text NOT NULL,
	"desc" text NOT NULL,
	singular text NOT NULL,
	family text NOT NULL,
	color text,
	shadow boolean NOT NULL,
	repolinks jsonb NOT NULL,
	packagelinks jsonb NOT NULL
);

CREATE UNIQUE INDEX ON repositories(name);

-- history
DROP TABLE IF EXISTS repositories_history CASCADE;

CREATE TABLE repositories_history (
	ts timestamp with time zone NOT NULL PRIMARY KEY,
	snapshot jsonb NOT NULL
);

--------------------------------------------------------------------------------
-- Tables binding metapackages and other entities
--------------------------------------------------------------------------------

-- per-repository
DROP TABLE IF EXISTS repo_metapackages CASCADE;

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
DROP TABLE IF EXISTS category_metapackages CASCADE;

CREATE TABLE category_metapackages (
	category text NOT NULL,
	effname text NOT NULL,
	"unique" boolean NOT NULL,

	PRIMARY KEY(category, effname)
);

CREATE INDEX ON category_metapackages(effname);

-- per-maintainer
DROP TABLE IF EXISTS maintainer_metapackages CASCADE;

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
-- Additional derived tables
--------------------------------------------------------------------------------
DROP TABLE IF EXISTS maintainer_repo_metapackages CASCADE;

CREATE TABLE maintainer_repo_metapackages (
	maintainer_id integer NOT NULL,
	repository_id smallint NOT NULL,
	metapackage_id integer NOT NULL,

	first_seen timestamp with time zone NOT NULL,
	last_seen timestamp with time zone NOT NULL,

	versions_uptodate text[],
	versions_outdated text[],
	versions_ignored text[],

	PRIMARY KEY(maintainer_id, repository_id, metapackage_id)
);

-- events
DROP TABLE IF EXISTS maintainer_repo_metapackages_events CASCADE;

CREATE TABLE maintainer_repo_metapackages_events (
	id integer GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,

	maintainer_id integer NOT NULL,
	repository_id smallint NOT NULL,

	ts timestamp with time zone NOT NULL,

	metapackage_id integer NOT NULL,
	type maintainer_repo_metapackages_event_type NOT NULL,
	data jsonb NOT NULL
);

CREATE INDEX ON maintainer_repo_metapackages_events(maintainer_id, repository_id, ts DESC, type DESC);

-- triggers
CREATE TRIGGER maintainer_repo_metapackage_addremove
	AFTER INSERT OR DELETE ON maintainer_repo_metapackages
	FOR EACH ROW
EXECUTE PROCEDURE maintainer_repo_metapackages_create_events_trigger();

CREATE TRIGGER maintainer_repo_metapackage_update
	AFTER UPDATE ON maintainer_repo_metapackages
	FOR EACH ROW WHEN (
		OLD.versions_uptodate IS DISTINCT FROM NEW.versions_uptodate OR
		OLD.versions_outdated IS DISTINCT FROM NEW.versions_outdated OR
		OLD.versions_ignored IS DISTINCT FROM NEW.versions_ignored
	)
EXECUTE PROCEDURE maintainer_repo_metapackages_create_events_trigger();

--------------------------------------------------------------------------------
-- Statistics
--------------------------------------------------------------------------------
DROP TABLE IF EXISTS statistics CASCADE;

CREATE TABLE statistics (
	num_packages integer NOT NULL DEFAULT 0,
	num_metapackages integer NOT NULL DEFAULT 0,
	num_problems integer NOT NULL DEFAULT 0,
	num_maintainers integer NOT NULL DEFAULT 0
);

INSERT INTO statistics VALUES(DEFAULT);

-- statistics_history
DROP TABLE IF EXISTS statistics_history CASCADE;

CREATE TABLE statistics_history (
	ts timestamp with time zone NOT NULL PRIMARY KEY,
	snapshot jsonb NOT NULL
);

--------------------------------------------------------------------------------
-- Links
--------------------------------------------------------------------------------
DROP TABLE IF EXISTS links CASCADE;

CREATE TABLE links (
	url text NOT NULL PRIMARY KEY,
	first_extracted timestamp with time zone NOT NULL DEFAULT now(),
	last_extracted timestamp with time zone NOT NULL DEFAULT now(),
	next_check timestamp with time zone NOT NULL DEFAULT now(),
	last_checked timestamp with time zone,

	ipv4_last_success timestamp with time zone,
	ipv4_last_failure timestamp with time zone,
	ipv4_success boolean,
	ipv4_status_code smallint,
	ipv4_permanent_redirect_target text,

	ipv6_last_success timestamp with time zone,
	ipv6_last_failure timestamp with time zone,
	ipv6_success boolean,
	ipv6_status_code smallint,
	ipv6_permanent_redirect_target text
);

CREATE INDEX ON links(next_check);

--------------------------------------------------------------------------------
-- Problems
--------------------------------------------------------------------------------
DROP TABLE IF EXISTS problems CASCADE;

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
DROP TABLE IF EXISTS reports CASCADE;

CREATE TABLE IF NOT EXISTS reports (
	id integer GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
	created timestamp with time zone NOT NULL,
	updated timestamp with time zone NOT NULL,
	client text,
	effname text NOT NULL,
	need_verignore boolean NOT NULL,
	need_split boolean NOT NULL,
	need_merge boolean NOT NULL,
	comment text,
	reply text,
	accepted boolean
);

CREATE INDEX ON reports(effname, created DESC);
CREATE INDEX ON reports(created DESC) WHERE (accepted IS NULL);
CREATE INDEX ON reports(updated DESC);

--------------------------------------------------------------------------------
-- Url relations
--------------------------------------------------------------------------------
DROP TABLE IF EXISTS url_relations CASCADE;

CREATE TABLE url_relations (
	metapackage_id integer NOT NULL,
	urlhash bigint NOT NULL,
	PRIMARY KEY(metapackage_id, urlhash)
);

CREATE INDEX ON url_relations(urlhash, metapackage_id);

--------------------------------------------------------------------------------
-- Updates
--------------------------------------------------------------------------------
DROP TABLE IF EXISTS repository_ruleset_hashes CASCADE;

CREATE TABLE repository_ruleset_hashes (
	repository text NOT NULL PRIMARY KEY,
	ruleset_hash text NULL
);
