-- Copyright (C) 2018 Paul Wise <pabs3@bonedaddy.net>
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
-- @param repo
-- @param package
--
-- @returns array of metapackages
--
--------------------------------------------------------------------------------
SELECT DISTINCT
	effname
FROM packages
WHERE repo = %(repo)s
AND name = %(package)s;
