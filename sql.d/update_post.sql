-- Copyright (C) 2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
-- Update extra tables
--------------------------------------------------------------------------------
INSERT
INTO maintainer_repo_metapackages (
	maintainer_id,
	repository_id,
	metapackage_id,

	first_seen,
	last_seen,

	versions_uptodate,
	versions_outdated,
	versions_ignored
)
SELECT
	(SELECT id FROM maintainers WHERE maintainer = tmp.maintainer),
	(SELECT id FROM repositories WHERE name = tmp.repo),
	(SELECT id FROM metapackages WHERE effname = tmp.effname),

	now(),
	now(),

	array_agg(DISTINCT version ORDER BY version) FILTER(WHERE versionclass IN (1, 4, 5)),
	array_agg(DISTINCT version ORDER BY version) FILTER(WHERE versionclass = 2),
	array_agg(DISTINCT version ORDER BY version) FILTER(WHERE versionclass IN (3, 7, 8))
FROM (
	SELECT
		repo,
		unnest(maintainers) AS maintainer,
		effname,
		version,
		versionclass
	FROM packages
) AS tmp
GROUP BY repo, maintainer, effname
ON CONFLICT (maintainer_id, repository_id, metapackage_id)
DO UPDATE SET
	versions_uptodate = EXCLUDED.versions_uptodate,
	versions_outdated = EXCLUDED.versions_outdated,
	versions_ignored = EXCLUDED.versions_ignored,

	last_seen = now();

DELETE
FROM maintainer_repo_metapackages
WHERE
	last_seen != now();

--------------------------------------------------------------------------------
-- Clean up unreferenced runs and logs
--------------------------------------------------------------------------------
WITH removed_runs AS (
	DELETE
	FROM runs
	WHERE
		NOT EXISTS (
			SELECT
				*
			FROM repositories
			WHERE
				current_run_id = runs.id OR
				last_successful_fetch_run_id = runs.id OR
				last_failed_fetch_run_id = runs.id OR
				last_successful_parse_run_id = runs.id OR
				last_failed_parse_run_id = runs.id
		)
	RETURNING
		id
)
DELETE
FROM log_lines
WHERE run_id IN (
	SELECT id FROM removed_runs
);
