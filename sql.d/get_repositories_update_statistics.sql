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
--
-- @returns array of dicts
--
--------------------------------------------------------------------------------
SELECT
	name,

	last_fetch_subq.id AS last_fetch_id,
	now() - last_fetch_subq.start_ts AS last_fetch_ago,
	last_fetch_subq.status AS last_fetch_status,
	last_fetch_subq.num_errors AS last_fetch_errors,
	last_fetch_subq.num_warnings AS last_fetch_warnings,

	last_parse_subq.id AS last_parse_id,
	now() - last_parse_subq.start_ts AS last_parse_ago,
	last_parse_subq.status AS last_parse_status,
	last_parse_subq.num_errors AS last_parse_errors,
	last_parse_subq.num_warnings AS last_parse_warnings,

	last_failed_subq.id AS last_failed_id,
	now() - last_failed_subq.start_ts AS last_failed_ago,
	last_failed_subq.status AS last_failed_status,
	last_failed_subq.num_errors AS last_failed_errors,
	last_failed_subq.num_warnings AS last_failed_warnings,

	(
		SELECT
			array_agg(json)
		FROM (
			SELECT
				json
			FROM (
				SELECT
					start_ts,
					json_build_object(
						'id', id,
						'status', status,
						'type', "type",
						'no_changes', no_changes
					) AS json
				FROM
					runs
				WHERE repository_id = repositories.id
				ORDER BY start_ts DESC
				LIMIT 14
			) AS tmp1
			ORDER by start_ts
		) AS tmp
	) AS history
FROM repositories
LEFT JOIN (
	SELECT
		*,
		row_number() over(PARTITION BY repository_id ORDER BY start_ts DESC) AS rn
	FROM runs
	WHERE status = 'failed'::run_status
) last_failed_subq ON last_failed_subq.repository_id = repositories.id AND last_failed_subq.rn = 1
LEFT JOIN (
	SELECT
		*,
		row_number() over(PARTITION BY repository_id ORDER BY start_ts DESC) AS rn
	FROM runs
	WHERE type = 'fetch'::run_type AND status != 'interrupted'::run_status
) last_fetch_subq ON last_fetch_subq.repository_id = repositories.id AND last_fetch_subq.rn = 1
LEFT JOIN (
	SELECT
		*,
		row_number() over(PARTITION BY repository_id ORDER BY start_ts DESC) AS rn
	FROM runs
	WHERE type = 'parse'::run_type AND status != 'interrupted'::run_status
) last_parse_subq ON last_parse_subq.repository_id = repositories.id AND last_parse_subq.rn = 1
WHERE state != 'legacy'::repository_state
ORDER BY sortname;
