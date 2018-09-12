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
-- @returns array of dicts
--
--------------------------------------------------------------------------------
SELECT
	name,

	current_run_id,
    last_successful_fetch_run_id,
    last_failed_fetch_run_id,
    last_successful_parse_run_id,
    last_failed_parse_run_id,

	now() - current_run.start_ts AS current_run_duration,
	current_run.type AS current_run_type,

	now() - last_successful_fetch_run.finish_ts AS last_successful_fetch_ago,
	last_successful_fetch_run.num_warnings AS last_successful_fetch_warnings,
	last_successful_fetch_run.num_errors AS last_successful_fetch_errors,

	now() - last_failed_fetch_run.finish_ts AS last_failed_fetch_ago,
	last_failed_fetch_run.num_warnings AS last_failed_fetch_warnings,
	last_failed_fetch_run.num_errors AS last_failed_fetch_errors,

	now() - last_successful_parse_run.finish_ts AS last_successful_parse_ago,
	last_successful_parse_run.num_warnings AS last_successful_parse_warnings,
	last_successful_parse_run.num_errors AS last_successful_parse_errors,

	now() - last_failed_parse_run.finish_ts AS last_failed_parse_ago,
	last_failed_parse_run.num_warnings AS last_failed_parse_warnings,
	last_failed_parse_run.num_errors AS last_failed_parse_errors,

	CASE WHEN length(fetch_history) = 0 THEN 0.0 ELSE 100.0 * length(replace(fetch_history, 's', '')) / length(fetch_history) END AS fetch_failure_rate,
	CASE WHEN length(parse_history) = 0 THEN 0.0 ELSE 100.0 * length(replace(parse_history, 's', '')) / length(parse_history) END AS parse_failure_rate
FROM repositories
LEFT JOIN runs AS current_run ON (current_run.id = current_run_id)
LEFT JOIN runs AS last_successful_fetch_run ON (last_successful_fetch_run.id = last_successful_fetch_run_id)
LEFT JOIN runs AS last_failed_fetch_run ON (last_failed_fetch_run.id = last_failed_fetch_run_id)
LEFT JOIN runs AS last_successful_parse_run ON (last_successful_parse_run.id = last_successful_parse_run_id)
LEFT JOIN runs AS last_failed_parse_run ON (last_failed_parse_run.id = last_failed_parse_run_id)
WHERE state != 'legacy'::repository_state
ORDER BY sortname;
