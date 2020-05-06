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
DELETE FROM repo_metapackages
{% if partial %}
WHERE effname IN (SELECT effname FROM changed_projects)
{% endif %}
;

INSERT INTO repo_metapackages(
	repository_id,
	effname,

	newest,
	outdated,
	problematic,
	"unique",

	vulnerable
)
SELECT
	(SELECT id FROM repositories WHERE name = repo) AS repository_id,
	effname,

	count(*) FILTER (WHERE versionclass = 1 OR versionclass = 4 OR versionclass = 5) > 0,
	count(*) FILTER (WHERE versionclass = 2) > 0,
	count(*) FILTER (WHERE versionclass = 3 OR versionclass = 7 OR versionclass = 8) > 0,

	max(num_families) = 1,

	count(*) FILTER (WHERE (flags & (1 << 16))::boolean) > 0
FROM
	{% if partial %}incoming_packages{% else %}packages{% endif %}
	INNER JOIN metapackages USING(effname)
WHERE num_repos_nonshadow > 0
GROUP BY effname, repo
-- Reorder according to primary key
-- * Avoids thrashing when HashAggregate is used before data is inserted
-- * Leads to better query performance (see repology-benchmark)
ORDER BY repository_id, effname;

{% if analyze %}
ANALYZE repo_metapackages;
{% endif %}
