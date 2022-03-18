-- Copyright (C) 2020 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
-- @param history_cutoff_timestamp
--------------------------------------------------------------------------------

WITH old AS (
	SELECT
		effname,
		-- XXX: technical dept warning: since we don't distinguish "newest unique" and "devel unique" statuses, we have
		-- to use flags here. Better solution should be implemented in future
		array_agg(DISTINCT version ORDER BY version) FILTER(
			WHERE versionclass = 5 OR (versionclass = 4 AND (flags & 2)::bool)
		) AS devel_versions,
		array_agg(DISTINCT repo ORDER BY repo) FILTER(
			WHERE versionclass = 5 OR (versionclass = 4 AND (flags & 2)::bool)
		) AS devel_repos,
		array_agg(DISTINCT version ORDER BY version) FILTER(
			WHERE versionclass = 1 OR (versionclass = 4 AND NOT (flags & 2)::bool)
		) AS newest_versions,
		array_agg(DISTINCT repo ORDER BY repo) FILTER(
			WHERE versionclass = 1 OR (versionclass = 4 AND NOT (flags & 2)::bool)
		) AS newest_repos,
		array_agg(DISTINCT repo ORDER BY repo) AS all_repos
	FROM old_packages
	GROUP BY effname
), new AS (
	SELECT
		effname,
	    array_agg(DISTINCT version ORDER BY version) FILTER(
			WHERE versionclass = 5 OR (versionclass = 4 AND (flags & 2)::bool)
		) AS devel_versions,
		array_agg(DISTINCT repo ORDER BY repo) FILTER(
			WHERE versionclass = 5 OR (versionclass = 4 AND (flags & 2)::bool)
		) AS devel_repos,
		array_agg(DISTINCT version ORDER BY version) FILTER(
			WHERE versionclass = 1 OR (versionclass = 4 AND NOT (flags & 2)::bool)
		) AS newest_versions,
		array_agg(DISTINCT repo ORDER BY repo) FILTER(
			WHERE versionclass = 1 OR (versionclass = 4 AND NOT (flags & 2)::bool)
		) AS newest_repos,
		array_agg(DISTINCT repo ORDER BY repo) AS all_repos
	FROM incoming_packages
	GROUP BY effname
), diff AS (
	SELECT
		-- effname
		effname,

		-- flags
		old.effname IS NULL AS is_added,
		new.effname IS NULL AS is_removed,
		old.effname IS NOT NULL AND new.effname IS NOT NULL AS is_changed,
		-- XXX: these do NOT take alternative versions into account
		version_set_changed(old.devel_versions, new.devel_versions) AS is_devel_update,
		version_set_changed(old.newest_versions, new.newest_versions) AS is_newest_update,

		-- new state
		new.devel_versions AS devel_versions,
		new.devel_repos AS devel_repos,
		new.newest_versions AS newest_versions,
		new.newest_repos AS newest_repos,
		new.all_repos AS all_repos,

		-- old state
		old.all_repos AS old_all_repos,

		old.devel_versions[1] AS prev_devel_version,
		old.newest_versions[1] AS prev_newest_version,

		-- delta
		get_added_repos_for_projects_feed(old.all_repos, new.all_repos) AS added_repos,
		get_added_repos_for_projects_feed(new.all_repos, old.all_repos) AS removed_repos,
		get_added_repos_for_projects_feed(old.devel_repos, new.devel_repos) AS devel_catchup,
		get_added_repos_for_projects_feed(old.newest_repos, new.newest_repos) AS newest_catchup,
		EXISTS(SELECT unnest(new.devel_repos) INTERSECT SELECT unnest(old.all_repos)) AS devel_repo_seen_before,
		EXISTS(SELECT unnest(new.newest_repos) INTERSECT SELECT unnest(old.all_repos)) AS newest_repo_seen_before
	FROM old FULL OUTER JOIN new USING(effname)
)
INSERT INTO metapackages_events (
	effname,
	ts,
	type,
	data
)
--------------------------------------------------------------------------------
-- history_start
--------------------------------------------------------------------------------
SELECT
	effname,
	now(),
	'history_start'::metapackage_event_type,
	jsonb_strip_nulls(jsonb_build_object(
		'devel_versions', devel_versions,
		'newest_versions', newest_versions,
		'devel_repos', devel_repos,
		'newest_repos', newest_repos,
		'all_repos', all_repos
	))
FROM diff WHERE is_added
--------------------------------------------------------------------------------
-- history_end
--------------------------------------------------------------------------------
UNION ALL
SELECT
	effname,
	now(),
	'history_end'::metapackage_event_type,
	jsonb_strip_nulls(jsonb_build_object(
		'last_repos', old_all_repos
	))
FROM diff WHERE is_removed
--------------------------------------------------------------------------------
-- repos_update
--------------------------------------------------------------------------------
UNION ALL
SELECT
	effname,
	now(),
	'repos_update'::metapackage_event_type,
	jsonb_strip_nulls(jsonb_build_object(
		'repos_added', added_repos,
		'repos_removed', removed_repos
	))
FROM diff WHERE is_changed AND (added_repos != removed_repos)
--------------------------------------------------------------------------------
-- versions_update for devel
--------------------------------------------------------------------------------
UNION ALL
SELECT
	effname,
	now(),
	'version_update'::metapackage_event_type,
	jsonb_strip_nulls(jsonb_build_object(
		'branch', 'devel',
		'versions', devel_versions,
		'repos', devel_repos,
		'passed',
			nullifless(
				CASE
					WHEN devel_repo_seen_before
					THEN
						extract(epoch FROM
							now() - (
								SELECT trusted_start_ts
								FROM project_releases
								WHERE project_releases.effname = diff.effname AND project_releases.version = diff.prev_devel_version
							)
						)
					ELSE NULL
				END,
				%(history_cutoff_timestamp)s
			)
	))
FROM diff WHERE is_changed AND is_devel_update
--------------------------------------------------------------------------------
-- catch_up for devel
--------------------------------------------------------------------------------
UNION ALL
SELECT
	effname,
	now(),
	'catch_up'::metapackage_event_type,
	jsonb_strip_nulls(jsonb_build_object(
		'branch', 'devel',
		'repos', devel_catchup,
		'lag',
			nullifless(
				CASE
					WHEN devel_repo_seen_before
					THEN
						extract(epoch FROM
							now() - (
								SELECT trusted_start_ts
								FROM project_releases
								WHERE project_releases.effname = diff.effname AND project_releases.version = diff.prev_devel_version
							)
						)
					ELSE NULL
				END,
				%(history_cutoff_timestamp)s
			)
	))
FROM diff WHERE is_changed AND NOT is_devel_update AND devel_catchup != '{}'
--------------------------------------------------------------------------------
-- versions_update for newest
--------------------------------------------------------------------------------
UNION ALL
SELECT
	effname,
	now(),
	'version_update'::metapackage_event_type,
	jsonb_strip_nulls(jsonb_build_object(
		'branch', 'newest',
		'versions', newest_versions,
		'repos', newest_repos,
		'passed',
			nullifless(
				CASE
					WHEN newest_repo_seen_before
					THEN
						extract(epoch FROM
							now() - (
								SELECT trusted_start_ts
								FROM project_releases
								WHERE project_releases.effname = diff.effname AND project_releases.version = diff.prev_newest_version
							)
						)
					ELSE NULL
				END,
				%(history_cutoff_timestamp)s
			)
	))
FROM diff WHERE is_changed AND is_newest_update
--------------------------------------------------------------------------------
-- catch_up for newest
--------------------------------------------------------------------------------
UNION ALL
SELECT
	effname,
	now(),
	'catch_up'::metapackage_event_type,
	jsonb_strip_nulls(jsonb_build_object(
		'branch', 'newest',
		'repos', newest_catchup,
		'lag',
			nullifless(
				CASE
					WHEN newest_repo_seen_before
					THEN
						extract(epoch FROM
							now() - (
								SELECT trusted_start_ts
								FROM project_releases
								WHERE project_releases.effname = diff.effname AND project_releases.version = diff.prev_newest_version
							)
						)
					ELSE NULL
				END,
				%(history_cutoff_timestamp)s
			)
	))
FROM diff WHERE is_changed AND NOT is_newest_update AND newest_catchup != '{}'
;
