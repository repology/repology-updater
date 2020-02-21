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

-- create new
INSERT INTO metapackages(effname)
SELECT effname
FROM metapackages RIGHT OUTER JOIN changed_projects USING(effname)
WHERE metapackages.effname IS NULL
ON CONFLICT(effname) DO NOTHING;

-- update
UPDATE metapackages
SET
	num_repos = tmp.num_repos,
	num_repos_nonshadow = tmp.num_repos_nonshadow,
	num_families = tmp.num_families,
	num_repos_newest = tmp.num_repos_newest,
	num_families_newest = tmp.num_families_newest,

	orphaned_at = NULL
FROM (
	SELECT
		effname,
		count(DISTINCT repo) AS num_repos,
		count(DISTINCT repo) FILTER (WHERE NOT shadow) AS num_repos_nonshadow,
		count(DISTINCT family) AS num_families,
		count(DISTINCT repo) FILTER (WHERE versionclass = 1 OR versionclass = 5) AS num_repos_newest,
		count(DISTINCT family) FILTER (WHERE versionclass = 1 OR versionclass = 5) AS num_families_newest
	FROM incoming_packages
	GROUP BY effname
) AS tmp
WHERE metapackages.effname = tmp.effname;

-- orphan
UPDATE metapackages
SET
	num_repos = 0,
	num_repos_nonshadow = 0,
	num_families = 0,
	num_repos_newest = 0,
	num_families_newest = 0,

	has_related = false,

	orphaned_at = now()
FROM (SELECT DISTINCT effname FROM incoming_packages) alive_projects RIGHT OUTER JOIN changed_projects USING(effname)
WHERE metapackages.effname = changed_projects.effname AND alive_projects.effname IS NULL;

{% if analyze %}
ANALYZE metapackages;
{% endif %}
