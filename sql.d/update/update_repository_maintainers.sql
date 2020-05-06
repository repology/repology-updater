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
DELETE FROM repository_project_maintainers
WHERE project_id IN (
	SELECT id FROM metapackages WHERE effname IN (SELECT effname FROM changed_projects)
);

INSERT INTO repository_project_maintainers (
	maintainer_id,
	repository_id,
	project_id
)
SELECT
	(SELECT id FROM maintainers WHERE maintainer = tmp.maintainer),
	(SELECT id FROM repositories WHERE name = tmp.repo),
	(SELECT id FROM metapackages WHERE effname = tmp.effname)
FROM (
	SELECT DISTINCT
		unnest(maintainers) AS maintainer,
		repo,
		effname
	FROM incoming_packages
) AS tmp;

{% if analyze %}
ANALYZE repository_project_maintainers;
{% endif %}
