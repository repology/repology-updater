-- Copyright (C) 2018-2020 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
				PARTITION BY repository_id, type, status
				ORDER BY start_ts DESC
			) AS status_depth
		FROM runs
	) AS tmp
	WHERE
		-- keep failed runs for some time (assuming someone may keep a link to them)
		(status = 'failed'::run_status AND start_ts > now() - INTERVAL '31' DAY) OR
		-- keep last run of each kind (limiting age here allows last failed runs to expire)
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
-- Clean up stale links
--------------------------------------------------------------------------------
DELETE FROM links
WHERE refcount = 0 AND orphaned_since < now() - INTERVAL '1' MONTH;

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
	num_projects_problematic,
	num_projects_vulnerable
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
        FROM repositories_history
		-- Don't unnecessarily thin out the whole table each time -
		-- just process last week worth of history. This may produce
		-- leftovers for repostories which had no stat changes for more
		-- than a week, but that's not fatal
		WHERE ts > now() - interval '7' day
        WINDOW w AS (PARTITION by repository_id ORDER BY ts)
    ) AS tmp
    WHERE cur = next AND cur = prev
)
DELETE FROM repositories_history USING duplicate_rows
WHERE
	repositories_history.repository_id = duplicate_rows.repository_id AND
	repositories_history.ts = duplicate_rows.ts;

{#
do it manually for now
--------------------------------------------------------------------------------
-- Archive old events (maintainer and repository)
-- Note that project events are not processed, as project history is more
-- important
--------------------------------------------------------------------------------
WITH moved AS (
    DELETE FROM maintainer_repo_metapackages_events
    WHERE ts < now() - interval '1' year
    RETURNING maintainer_id, repository_id, ts, metapackage_id, type, data
)
INSERT INTO maintainer_repo_metapackages_events_archive(maintainer_id, repository_id, ts, metapackage_id, type, data)
SELECT * FROM moved;

WITH moved AS (
    DELETE FROM repository_events
    WHERE ts < now() - interval '1' year
    RETURNING repository_id, ts, metapackage_id, type, data
)
INSERT INTO repository_events_archive(repository_id, ts, metapackage_id, type, data)
SELECT * FROM moved;
#}

--------------------------------------------------------------------------------
-- For projects moved from <foo>-unclassified to <foo>-<bar>, add redirects from <foo> to <foo>-<bar> as well
--------------------------------------------------------------------------------
INSERT INTO project_redirects(project_id, repository_id, is_actual, trackname)
SELECT
    classified_p.id,
    unclassified_r.repository_id AS repository_id,
    false,
    unclassified_r.trackname AS trackname
FROM metapackages AS unclassified_p
INNER JOIN metapackages AS classified_p ON (classified_p.effname = substring(unclassified_p.effname, 0, length(unclassified_p.effname) - 12))
INNER JOIN project_redirects AS unclassified_r ON (unclassified_r.project_id = unclassified_p.id)
LEFT JOIN project_redirects AS classified_r ON (classified_r.project_id = classified_p.id AND classified_r.trackname = unclassified_r.trackname AND classified_r.repository_id = unclassified_r.repository_id)
WHERE
    unclassified_p.effname LIKE '%%-unclassified'
    AND unclassified_r.is_actual = false
    AND classified_r.is_actual is null;
