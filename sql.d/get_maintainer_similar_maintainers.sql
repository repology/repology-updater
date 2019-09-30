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
-- @param maintainer
-- @param limit
--
-- @returns array of dicts
--
--------------------------------------------------------------------------------

-- this obscure request needs some clarification
--
-- what we calculate as score here is actually Jaccard index
-- (see wikipedia) for two sets (of projects maintained by
-- two maintainers)
--
-- let M = set of projects for maintainer passed to this function
-- let C = set of projects for other maintainer we test for similarity
--
-- score = |M⋂C| / |M⋃C| = |M⋂C| / (|M| + |C| - |M⋂C|)
--
-- - num_projects_common is |M⋂C|
-- - num_projects is |C|
-- - sub-select just gets |M|
-- - the divisor thus is |M⋃C| = |M| + |C| - |M⋂C|
SELECT
	maintainer,
	num_projects_common AS count,
	100.0 * num_projects_common / (
		num_projects - num_projects_common + (
			SELECT num_projects
			FROM maintainers
			WHERE maintainer = %(maintainer)s
		)
	) AS match
FROM
	(
		SELECT
			maintainer_id,
			count(*) AS num_projects_common
		FROM
			maintainer_metapackages
		WHERE
			maintainer_id != (SELECT id FROM maintainers WHERE maintainer = %(maintainer)s) AND
			effname IN (
				SELECT
					effname
				FROM maintainer_metapackages
				WHERE maintainer_id = (SELECT id FROM maintainers WHERE maintainer = %(maintainer)s)
			)
		GROUP BY maintainer_id
	) AS intersecting_counts
	INNER JOIN maintainers ON(maintainer_id = maintainers.id)
ORDER BY match DESC
LIMIT %(limit)s;
