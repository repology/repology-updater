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

-- name: extract_links

INSERT INTO links(
	url,
	first_extracted,
	last_extracted
)
SELECT
	unnest(downloads),
	now(),
	now()
FROM packages
UNION
SELECT
	homepage,
	now(),
	now()
FROM packages
WHERE
	homepage IS NOT NULL AND
	repo NOT IN('cpan', 'pypi', 'rubygems', 'hackage', 'cran')
ON CONFLICT (url)
DO UPDATE SET
	last_extracted = now();
