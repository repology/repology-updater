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
-- @param reponame
-- @param run_id
-- @param run_type
-- @param success=True
--
--------------------------------------------------------------------------------
UPDATE repositories
SET
{% if run_type == 'current' %}
    current_run_id
{% elif run_type == 'fetch' and success %}
    last_successful_fetch_run_id
{% elif run_type == 'fetch' and not success %}
    last_failed_fetch_run_id
{% elif run_type == 'parse' and success %}
    last_successful_parse_run_id
{% elif run_type == 'parse' and not success %}
    last_failed_parse_run_id
{% endif %}
		= %(run_id)s
{% if run_type == 'fetch' %}
	, fetch_history = right(fetch_history || CASE WHEN %(success)s THEN 's' ELSE 'f' END, 10)
{% elif run_type == 'parse' %}
	, parse_history = right(parse_history || CASE WHEN %(success)s THEN 's' ELSE 'f' END, 10)
{% endif %}
WHERE
	name = %(reponame)s;
