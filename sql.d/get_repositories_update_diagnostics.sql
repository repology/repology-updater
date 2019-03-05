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

	fetch_run.id as fetch_run_id,
	fetch_run.finish_ts - fetch_run.start_ts AS fetch_duration,
	fetch_run.utime AS fetch_utime,
	fetch_run.stime AS fetch_stime,
	fetch_run.maxrss AS fetch_maxrss,
	CASE fetch_run.maxrss_delta WHEN 0 THEN NULL ELSE fetch_run.maxrss END AS fetch_maxrss_reliable,

	parse_run.id as parse_run_id,
	parse_run.finish_ts - parse_run.start_ts AS parse_duration,
	parse_run.utime AS parse_utime,
	parse_run.stime AS parse_stime,
	parse_run.maxrss AS parse_maxrss,
	CASE parse_run.maxrss_delta WHEN 0 THEN NULL ELSE parse_run.maxrss END AS parse_maxrss_reliable
FROM repositories
LEFT JOIN (
	SELECT
        *,
        row_number() over(PARTITION BY repository_id ORDER BY start_ts DESC) AS rn
    FROM runs
    WHERE successful AND type='fetch'::run_type
) fetch_run ON fetch_run.repository_id = repositories.id AND fetch_run.rn = 1
LEFT JOIN (
	SELECT
        *,
        row_number() over(PARTITION BY repository_id ORDER BY start_ts DESC) AS rn
    FROM runs
    WHERE successful AND type='parse'::run_type
) parse_run ON parse_run.repository_id = repositories.id AND parse_run.rn = 1
WHERE state != 'legacy'::repository_state
ORDER BY sortname;
