-- Copyright (C) 2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
-- @param repo
-- @param limit=None
--
-- @returns array of dicts
--
--------------------------------------------------------------------------------
SELECT
	id,
	ts,
	(SELECT effname FROM metapackages WHERE id = metapackage_id) AS effname,
	type,
	data
FROM maintainer_repo_metapackages_events
WHERE
	maintainer_id = (SELECT id FROM maintainers WHERE maintainer = %(maintainer)s) AND
	repository_id = (SELECT id FROM repositories WHERE name = %(repo)s)
ORDER BY ts DESC, type DESC
LIMIT %(limit)s;
