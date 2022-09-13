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

WITH old_links AS (
	SELECT
		(json_array_elements(links)->>0)::integer AS link_type,
		(json_array_elements(links)->>1)::integer AS link_id
	FROM old_packages
), new_links AS (
	SELECT
		(json_array_elements(links)->>0)::integer AS link_type,
		(json_array_elements(links)->>1)::integer AS link_id
	FROM incoming_packages
), old AS (
	SELECT
		link_id,
		bool_or(link_type IN (0, 1, 2, 3, 16, 17, 19, 20, 21, 22, 23)) AS priority,
		count(*) AS refcount
	FROM old_links
	GROUP BY link_id
), new AS (
	SELECT
		link_id,
		bool_or(link_type IN (0, 1, 2, 3, 16, 17, 19, 20, 21, 22, 23)) AS priority,
		count(*) AS refcount
	FROM new_links
	GROUP BY link_id
), delta AS (
	SELECT
		link_id,
		coalesce(new.refcount, 0) - coalesce(old.refcount, 0) AS delta_refcount,
		new.priority AS priority
	FROM old FULL OUTER JOIN new USING(link_id)
	WHERE
		coalesce(new.refcount, 0) != coalesce(old.refcount, 0)
		OR new.priority > old.priority
)
UPDATE links
SET
	refcount = refcount + delta_refcount,
	priority = links.priority OR coalesce(delta.priority, false),
	orphaned_since = CASE WHEN refcount + delta_refcount = 0 THEN now() ELSE NULL END
FROM delta
WHERE
	links.id = delta.link_id;

{% if analyze %}
ANALYZE links;
{% endif %}
