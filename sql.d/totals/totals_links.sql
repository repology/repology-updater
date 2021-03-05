-- Copyright (C) 2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
-- @param do_fix=False
-- @returns array of dicts
--------------------------------------------------------------------------------
WITH package_links AS (
	SELECT
        (json_array_elements(links)->>0)::integer AS link_type,
        (json_array_elements(links)->>1)::integer AS id
    FROM packages
), expected AS (
	SELECT
		id,
		bool_or(link_type IN (0, 1, 2, 3, 16, 17, 19, 20, 21, 22, 23)) AS priority,
		count(*) AS refcount
	FROM package_links
	GROUP BY id
)
{% if do_fix %}
-- note: these changes are not shown to SELECT below due to how CTE work
, fix AS (
	UPDATE links
	SET
		refcount = expected.refcount,
		priority = expected.priority
	FROM expected
	WHERE links.id = expected.id
)
{% endif %}
SELECT
	url AS key,
	row_to_json(actual) AS actual,
	row_to_json(expected) AS expected
FROM
	expected FULL OUTER JOIN links actual USING(id)
WHERE
	actual.refcount != coalesce(expected.refcount, 0)
	OR actual.priority != expected.priority
;
