-- Copyright (C) 2020 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
WITH old AS (
	SELECT DISTINCT
		effname,
		repo,
		trackname
	FROM old_packages
), new AS (
	SELECT DISTINCT
		effname,
		repo,
		trackname
	FROM incoming_packages
), diff AS (
	SELECT
		effname,
		repo,
		trackname,
		new.effname IS NOT NULL AS is_actual
	FROM old FULL OUTER JOIN new USING(effname, repo, trackname)
	WHERE (old.effname IS NULL OR new.effname IS NULL) AND
		repo IN (SELECT name FROM repositories WHERE state = 'active'::repository_state)
)
INSERT INTO project_redirects2 (
	project_id,
    repository_id,
    trackname,
    is_actual
)
SELECT
	(SELECT id FROM metapackages WHERE metapackages.effname = diff.effname) AS project_id,
	(SELECT id FROM repositories WHERE repositories.name = diff.repo) AS repository_id,
	trackname,
	is_actual
FROM diff
ON CONFLICT(project_id, repository_id, trackname)
DO UPDATE SET is_actual = EXCLUDED.is_actual;

{% if analyze %}
ANALYZE project_redirects2;
{% endif %}
