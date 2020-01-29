-- Copyright (C) 2016-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
-- Update related urls
--------------------------------------------------------------------------------
DELETE
FROM url_relations;

INSERT
INTO url_relations
SELECT
	metapackage_id,
	urlhash
FROM
(
	SELECT
		metapackage_id,
		urlhash,
		count(*) OVER (PARTITION BY urlhash) AS metapackages_for_url
	FROM
	(
		SELECT DISTINCT
			(SELECT id FROM metapackages WHERE metapackages.effname = packages.effname) AS metapackage_id,
			(
				'x' || left(
					md5(
						simplify_url(homepage)
					), 16
				)
			)::bit(64)::bigint AS urlhash
		FROM packages
		WHERE homepage ~ '^https?://'
	) AS tmp2
) AS tmp1
WHERE metapackages_for_url > 1;

ANALYZE url_relations;
