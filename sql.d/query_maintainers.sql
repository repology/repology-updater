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
-- @param pivot=None
-- @param reverse=False
-- @param search=None
-- @param limit=None
--
-- @returns array of dicts
--
--------------------------------------------------------------------------------
SELECT
	*
FROM (
	SELECT
		maintainer,
		bestrepo,
		bestrepo_num_projects,
		bestrepo_num_projects_newest,
		bestrepo_num_projects_outdated,
		bestrepo_num_projects_problematic,
		num_projects,
		num_repos,
		now() - first_seen AS first_seen_ago
	FROM maintainers
	WHERE
		(
			num_packages > 0
		{% if pivot %}
		) AND (
			-- pivot condition
			{% if reverse %}
			maintainer <= %(pivot)s
			{% else %}
			maintainer >= %(pivot)s
			{% endif %}
		{% endif %}
		{% if search %}
		) AND (
			-- search condition
			maintainer LIKE ('%%' || %(search)s || '%%')
		{% endif %}
		)
	ORDER BY
		maintainer{% if reverse %} DESC{% endif %}
	LIMIT %(limit)s
) AS tmp
ORDER BY maintainer;
