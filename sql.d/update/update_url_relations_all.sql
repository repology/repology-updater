-- Copyright (C) 2016-2020 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
-- @param analyze=True
--------------------------------------------------------------------------------
DELETE
FROM url_relations_all
WHERE metapackage_id IN (SELECT id FROM metapackages WHERE effname IN (SELECT effname FROM changed_projects));

WITH homepages AS (
	SELECT
		effname,
		(json_array_elements(links)->>0)::integer AS link_type,
		json_array_elements(links)->>1 AS url,
		family
	FROM incoming_packages_raw
), grouped AS (
	SELECT
		effname,
		(
			'x' || left(
				md5(
					simplify_url(url)
				), 16
			)
		)::bit(64)::bigint AS urlhash,
		count(DISTINCT family) AS num_families
	FROM homepages
	WHERE link_type IN(
		0,   -- UPSTREAM_HOMEPAGE
		--1, -- UPSTREAM_DOWNLOAD (may generate too many new entries)
		2,   -- UPSTREAM_REPOSITORY
		4,   -- PROJECT_HOMEPAGE
		16,  -- UPSTREAM_DOCUMENTATION
		20,  -- UPSTREAM_DISCUSSION
		23   -- UPSTREAM_WIKI
	)
	GROUP BY effname, urlhash
)
INSERT
INTO url_relations_all(metapackage_id, urlhash, weight)
SELECT
	(SELECT id FROM metapackages WHERE metapackages.effname = grouped.effname),
	urlhash,
	num_families::float / max(num_families) OVER (PARTITION BY effname)
FROM grouped;

{% if analyze %}
ANALYZE url_relations_all;
{% endif %}
