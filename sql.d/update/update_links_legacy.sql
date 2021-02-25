-- Copyright (C) 2016-2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

WITH old_raw AS (
	SELECT unnest(downloads) AS url
	FROM old_packages
	UNION ALL
	SELECT homepage AS url
	FROM old_packages
	WHERE
		homepage IS NOT NULL AND
		repo NOT IN('cpan', 'metacpan', 'rubygems', 'cran') AND
		-- nix spawns tons of these, while it should use canonical urls as suggested by CRAN
		homepage NOT LIKE '%%mran.revolutionanalytics.com/snapshot/20%%'
), new_raw AS (
	SELECT unnest(downloads) AS url
	FROM incoming_packages
	UNION ALL
	SELECT homepage AS url
	FROM incoming_packages
	WHERE
		homepage IS NOT NULL AND
		repo NOT IN('cpan', 'metacpan', 'rubygems', 'cran') AND
		-- nix spawns tons of these, while it should use canonical urls as suggested by CRAN
		homepage NOT LIKE '%%mran.revolutionanalytics.com/snapshot/20%%'
), old AS (
	SELECT
		url,
		count(*) AS refcount
	FROM old_raw
	GROUP BY url
), new AS (
	SELECT
		url,
		count(*) AS refcount
	FROM new_raw
	GROUP BY url
), delta AS (
	SELECT
		url,
		coalesce(new.refcount, 0) - coalesce(old.refcount, 0) AS delta_refcount
	FROM old FULL OUTER JOIN new USING(url)
	WHERE coalesce(new.refcount, 0) != coalesce(old.refcount, 0)
)
UPDATE links
SET
	refcount = refcount + delta_refcount,
	orphaned_since = CASE WHEN refcount + delta_refcount = 0 THEN now() ELSE NULL END
FROM delta
WHERE links.url = delta.url;

{% if analyze %}
ANALYZE links;
{% endif %}
