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
-- @param limit=None
--
-- @returns array of dicts
--
--------------------------------------------------------------------------------
SELECT
	effname,
	num_families,
	(num_families-1)/extract(epoch FROM now() - first_seen) * 60 * 60 * 24 * 7 AS rate
FROM metapackages
WHERE
	num_families > 1 AND num_families < 4
ORDER BY rate DESC, effname
LIMIT %(limit)s;
