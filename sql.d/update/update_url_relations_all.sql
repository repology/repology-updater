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

INSERT
INTO url_relations_all
SELECT
	metapackage_id,
	urlhash,
	num_families::float / max(num_families) OVER (PARTITION BY metapackage_id)
FROM (
	SELECT
		(SELECT id FROM metapackages WHERE metapackages.effname = incoming_packages.effname) AS metapackage_id,
		(
			'x' || left(
				md5(
					simplify_url(homepage)
				), 16
			)
		)::bit(64)::bigint AS urlhash,
		count(DISTINCT family) num_families
	FROM incoming_packages
	WHERE homepage ~ '^https?://'
	GROUP BY metapackage_id, urlhash
) AS tmp;

{% if analyze %}
ANALYZE url_relations_all;
{% endif %}
