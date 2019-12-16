-- Copyright (C) 2016-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
-- Update links
--------------------------------------------------------------------------------

-- extract fresh
INSERT INTO links(
	url
)
SELECT
	unnest(downloads)
FROM packages
UNION
SELECT
	homepage
FROM packages
WHERE
	homepage IS NOT NULL AND
	repo NOT IN('cpan', 'metacpan', 'pypi', 'rubygems', 'cran') AND
	homepage NOT LIKE '%%mran.revolutionanalytics.com/snapshot/20%%'  -- nix spawns tons of these, while it should use canonical urls as suggested by CRAN
ON CONFLICT (url)
DO UPDATE SET
	last_extracted = now();
