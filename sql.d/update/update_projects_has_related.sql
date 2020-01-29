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

-- XXX: AS METARIALIZED here yields a bit better performance;
-- may add it when we swith to Pg12 everywhere and require it
WITH metapackages_with_related AS (
	SELECT DISTINCT metapackage_id
	FROM url_relations
	WHERE EXISTS (
		SELECT *
		FROM url_relations related
		WHERE related.urlhash = url_relations.urlhash AND
			related.metapackage_id != url_relations.metapackage_id
	)
)
UPDATE metapackages
SET
	has_related = EXISTS (
		SELECT * FROM metapackages_with_related WHERE metapackages_with_related.metapackage_id = id
	)
WHERE
	has_related != EXISTS (
        SELECT * FROM metapackages_with_related WHERE metapackages_with_related.metapackage_id = id
    );
