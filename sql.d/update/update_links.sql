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

INSERT INTO links (
	url
)
SELECT
	unnest(downloads) AS url
FROM incoming_packages
UNION
SELECT
	homepage AS url
FROM incoming_packages
WHERE
	homepage IS NOT NULL AND
	repo NOT IN('cpan', 'metacpan', 'rubygems', 'cran') AND
	-- nix spawns tons of these, while it should use canonical urls as suggested by CRAN
	homepage NOT LIKE '%%mran.revolutionanalytics.com/snapshot/20%%'
-- XXX: might want to change following ON CONFLICT clause to
-- WHERE NOT EXISTS (SELECT * FROM links WHERE links.url = url)
-- as soon as we have generated id column for links table
ON CONFLICT(url) DO NOTHING;
