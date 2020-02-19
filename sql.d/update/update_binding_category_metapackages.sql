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
-- @param partial=False
-- @param analyze=True
--------------------------------------------------------------------------------
DELETE FROM category_metapackages
{% if partial %}
WHERE effname IN (SELECT effname FROM changed_projects)
{% endif %}
;

INSERT INTO category_metapackages (
	category,
	effname,
	"unique"
)
SELECT
	category,
	effname,
	max(num_families) = 1
FROM
	{% if partial %}incoming_packages{% else %}packages{% endif %}
	INNER JOIN metapackages USING(effname)
WHERE category IS NOT NULL AND num_repos_nonshadow > 0
GROUP BY effname, category
ORDER BY effname;

{% if analyze %}
ANALYZE category_metapackages;
{% endif %}
