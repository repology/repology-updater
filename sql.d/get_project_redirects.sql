-- Copyright (C) 2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
-- @param oldname
-- @param limit=None
--
-- @returns array of values
--
--------------------------------------------------------------------------------
SELECT
	newname
FROM project_redirects
WHERE
	oldname = %(oldname)s
	AND EXISTS (
		-- only return valid projects
		SELECT *
		FROM metapackages
		WHERE metapackages.effname = project_redirects.newname AND num_repos > 0
	)
LIMIT %(limit)s;
