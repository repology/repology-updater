-- Copyright (C) 2016-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
-- Update aggregate tables: metapackages, pass1
--------------------------------------------------------------------------------
INSERT
INTO metapackages (
	effname,
	num_repos,
	num_repos_nonshadow,
	num_families,
	num_repos_newest,
	num_families_newest,
	max_repos,
	max_families,
	first_seen,
	last_seen,

	devel_versions,
	devel_repos,
	devel_version_update,

	newest_versions,
	newest_repos,
	newest_version_update,

	all_repos
)
SELECT
	effname,
	count(DISTINCT repo),
	count(DISTINCT repo) FILTER (WHERE NOT shadow),
	count(DISTINCT family),
	count(DISTINCT repo) FILTER (WHERE versionclass = 1 OR versionclass = 5),
	count(DISTINCT family) FILTER (WHERE versionclass = 1 OR versionclass = 5),
	count(DISTINCT repo),
	count(DISTINCT family),
	now(),
	now(),

	-- XXX: technical dept warning: since we don't distinguish "newest unique" and "newest devel" statuses, we have
	-- to use flags here. Better solution should be implemented in future
	array_agg(DISTINCT version ORDER BY version) FILTER(WHERE versionclass = 5 OR (versionclass = 4 AND (flags & 2)::bool)),
	array_agg(DISTINCT repo ORDER BY repo) FILTER(WHERE versionclass = 5 OR (versionclass = 4 AND (flags & 2)::bool)),
	NULL,  -- first time we see this metapackage, time of version update is not known yet

	array_agg(DISTINCT version ORDER BY version) FILTER(WHERE versionclass = 1 OR (versionclass = 4 AND NOT (flags & 2)::bool)),
	array_agg(DISTINCT repo ORDER BY repo) FILTER(WHERE versionclass = 1 OR (versionclass = 4 AND NOT (flags & 2)::bool)),
	NULL,

	array_agg(DISTINCT repo ORDER BY repo)
FROM packages
GROUP BY effname
ON CONFLICT (effname)
DO UPDATE SET
	num_repos = EXCLUDED.num_repos,
	num_repos_nonshadow = EXCLUDED.num_repos_nonshadow,
	num_families = EXCLUDED.num_families,
	num_repos_newest = EXCLUDED.num_repos_newest,
	num_families_newest = EXCLUDED.num_families_newest,
	max_repos = greatest(metapackages.max_repos, EXCLUDED.num_repos),
	max_families = greatest(metapackages.max_families, EXCLUDED.num_families),
	last_seen = now(),
	orphaned_at = NULL,

	devel_versions = EXCLUDED.devel_versions,
	devel_repos = EXCLUDED.devel_repos,
	devel_version_update =
		-- We want version update time to be as reliable as possible so
		-- the policy is that it's better to have no known last update time
		-- than to have an incorrect one.
		--
		-- For instance, we want to ignore addition of new repo which has
		-- the greated version than we know and don't record this as an
		-- update, because actual update could've happened long ago.
		CASE
			WHEN
				-- no change (both defined and equal)
				version_compare2(EXCLUDED.devel_versions[1], metapackages.devel_versions[1]) = 0
			THEN metapackages.devel_version_update
			WHEN
				-- trusted update (both should be defined)
				version_compare2(EXCLUDED.devel_versions[1], metapackages.devel_versions[1]) > 0 AND
				EXCLUDED.devel_repos && metapackages.all_repos
			THEN now()
			ELSE NULL -- else reset
		END,

	newest_versions = EXCLUDED.newest_versions,
	newest_repos = EXCLUDED.newest_repos,
	newest_version_update =
		CASE
			WHEN
				-- no change (both defined and equal)
				version_compare2(EXCLUDED.newest_versions[1], metapackages.newest_versions[1]) = 0
			THEN metapackages.newest_version_update
			WHEN
				-- trusted update (both should be defined)
				version_compare2(EXCLUDED.newest_versions[1], metapackages.newest_versions[1]) > 0 AND
				EXCLUDED.newest_repos && metapackages.all_repos
			THEN now()
			ELSE NULL -- else reset
		END,

	all_repos = EXCLUDED.all_repos;

--------------------------------------------------------------------------------
-- Update aggregate tables: metapackages, finalize
--------------------------------------------------------------------------------
UPDATE metapackages
SET
	num_repos = 0,
	num_repos_nonshadow = 0,
	num_families = 0,
	num_repos_newest = 0,
	num_families_newest = 0,
	has_related = false,
	devel_versions = NULL,
	devel_repos = NULL,
	devel_version_update = NULL,
	newest_versions = NULL,
	newest_repos = NULL,
	newest_version_update = NULL,
	all_repos = NULL,
	orphaned_at = now()
WHERE
	last_seen != now();

ANALYZE metapackages;
