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
-- @param fromrepo
-- @param torepo
--
-- @returns array of tuples
--
--------------------------------------------------------------------------------
SELECT
	array_agg(DISTINCT frompkgs.name ORDER BY frompkgs.name) AS fromnames,
	array_agg(DISTINCT topkgs.name ORDER BY topkgs.name) AS tonames
FROM packages frompkgs
INNER JOIN packages topkgs USING (effname)
WHERE frompkgs.repo=%(fromrepo)s AND topkgs.repo=%(torepo)s
GROUP BY effname
HAVING array_agg(DISTINCT frompkgs.name ORDER BY frompkgs.name) != array_agg(DISTINCT topkgs.name ORDER BY topkgs.name)
ORDER BY fromnames;
