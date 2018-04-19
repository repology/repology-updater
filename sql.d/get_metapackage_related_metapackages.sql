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
-- @param effname
-- @param limit
--
-- @returns dict of dicts
--
--------------------------------------------------------------------------------
SELECT
	effname,
	num_families,
	has_related
FROM metapackages
WHERE id IN (
	WITH RECURSIVE r AS (
		SELECT
			metapackage_id,
			urlhash
		FROM url_relations
		WHERE metapackage_id = (SELECT id FROM metapackages WHERE effname = %(effname)s)
		UNION
		SELECT
			url_relations.metapackage_id,
			url_relations.urlhash
		FROM url_relations
		JOIN r ON
			url_relations.metapackage_id = r.metapackage_id OR url_relations.urlhash = r.urlhash
	)
	SELECT DISTINCT
		metapackage_id
	FROM r
	LIMIT %(limit)s
);
