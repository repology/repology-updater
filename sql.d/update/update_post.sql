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

--- XXX: don't mix up with maintainer_and_repo_metapackages table update from update_finish
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
-- Clean up old runs and logs
--------------------------------------------------------------------------------
WITH preserved_runs AS (
	SELECT
		id
	FROM (
		SELECT
			*,
			row_number() OVER (
				PARTITION BY repository_id
				ORDER BY start_ts DESC
			) AS depth,
			row_number() OVER (
				PARTITION BY repository_id, status
				ORDER BY start_ts DESC
			) AS status_depth
		FROM runs
	) AS tmp
	WHERE
		-- keep failed runs for some time (assuming someone may keep a link to them)
		(status = 'failed'::run_status AND start_ts > now() - INTERVAL '31' DAY) OR
		-- keep last run of any kind (limiting age here allows last failed runs to expire)
		(start_ts > now() - INTERVAL '31' DAY AND status_depth = 1) OR
		-- keep normal runs for some time
		(start_ts > now() - INTERVAL '3' DAY) OR
		-- always keep 20 latest runs
		(depth <= 20)
)
DELETE FROM runs
WHERE id NOT IN (
	SELECT id FROM preserved_runs
);

-- delete interrupted unfinished runs
DELETE FROM runs
WHERE finish_ts IS NULL AND start_ts < now() - INTERVAL '1' day;

DELETE FROM log_lines
WHERE run_id NOT IN (
	SELECT id FROM runs
);

--------------------------------------------------------------------------------
-- Update redirects
--------------------------------------------------------------------------------
INSERT
INTO project_redirects (
	oldname,
	newname
)
SELECT DISTINCT
	projectname_seed,
	effname
FROM packages
WHERE projectname_seed != effname
ON CONFLICT (oldname, newname) DO NOTHING;

--------------------------------------------------------------------------------
-- Clean up stale links
--------------------------------------------------------------------------------
DELETE FROM links
WHERE last_extracted < now() - INTERVAL '1' MONTH;

--------------------------------------------------------------------------------
-- Remove duplicate history entries
--------------------------------------------------------------------------------
{% macro fields() %}
	num_problems,
	num_maintainers,
	num_projects,
	num_projects_unique,
	num_projects_newest,
	num_projects_outdated,
	num_projects_comparable,
	num_projects_problematic
{% endmacro %}

WITH duplicate_rows AS (
    SELECT
        repository_id,
        ts
    FROM (
        SELECT
            repository_id,
            ts,
            row({{ fields() }}) AS cur,
            lead(row({{ fields() }}), 1) OVER w AS next,
            lag(row({{ fields() }}), 1) OVER w AS prev
        FROM repositories_history_new
		-- don't unnecessarily thin out whole table each time -
		-- just process last day worth of history
		WHERE ts > now() - interval '1' day
        WINDOW w AS (PARTITION by repository_id ORDER BY ts)
    ) AS tmp
    WHERE cur = next AND cur = prev
)
DELETE FROM repositories_history_new USING duplicate_rows
WHERE
	repositories_history_new.repository_id = duplicate_rows.repository_id AND
	repositories_history_new.ts = duplicate_rows.ts;
