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
-- @param analyze=True
--------------------------------------------------------------------------------

WITH "all" AS (
	SELECT DISTINCT json_array_elements(links)->>1 AS url FROM incoming_packages_raw
), new AS (
	SELECT url
	FROM "all"
	WHERE NOT EXISTS (
		SELECT *
		FROM links
		WHERE links.url = "all".url
	)
)
INSERT INTO links(url)
SELECT url
FROM new;

{% if analyze %}
ANALYZE links;
{% endif %}
