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
WITH expected AS (
	SELECT
		url,
		count(*) AS refcount
	FROM (
		SELECT unnest(downloads) AS url
		FROM packages
		UNION ALL
		SELECT homepage AS url
		FROM packages
		WHERE
			homepage IS NOT NULL AND
			repo NOT IN('cpan', 'metacpan', 'rubygems', 'cran') AND
			-- nix spawns tons of these, while it should use canonical urls as suggested by CRAN
			homepage NOT LIKE '%%mran.revolutionanalytics.com/snapshot/20%%'
	) AS raw
	GROUP BY url
)
{% if do_fix %}
-- note: these changes are not shown to SELECT below due to how CTE work
, fix AS (
	UPDATE links
	SET
		refcount = expected.refcount
	FROM expected
	WHERE links.url = expected.url
)
{% endif %}
SELECT
	url,
	row_to_json(actual) AS actual,
	row_to_json(expected) AS expected
FROM
	expected FULL OUTER JOIN links actual using(url)
WHERE
	actual.refcount != coalesce(expected.refcount, 0)
;
