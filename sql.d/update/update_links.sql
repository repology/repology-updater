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

WITH old AS (
	SELECT
		(json_array_elements(links)->>1)::integer AS link_id,
		count(*) AS refcount
	FROM old_packages
	GROUP BY link_id
), new AS (
	SELECT
		(json_array_elements(links)->>1)::integer AS link_id,
		count(*) AS refcount
	FROM incoming_packages
	GROUP BY link_id
), delta AS (
	SELECT
		link_id,
		coalesce(new.refcount, 0) - coalesce(old.refcount, 0) AS delta_refcount
	FROM old FULL OUTER JOIN new USING(link_id)
	WHERE coalesce(new.refcount, 0) != coalesce(old.refcount, 0)
)
UPDATE links
SET
	refcount = refcount + delta_refcount,
	orphaned_since = CASE WHEN refcount + delta_refcount = 0 THEN now() ELSE NULL END
FROM delta
WHERE links.id = delta.link_id;

{% if analyze %}
ANALYZE links;
{% endif %}
