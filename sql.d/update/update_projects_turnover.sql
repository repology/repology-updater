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

INSERT INTO project_turnover (
	effname,
	delta,
	family
)
SELECT
	effname,
	-1,
	family
FROM (
	SELECT
		effname,
		(SELECT id FROM repositories WHERE repositories.name = repo) AS repository_id,
		trackname,
		family
	FROM old_packages
	WHERE (SELECT state FROM repositories WHERE repositories.name = repo) = 'active'
) AS tmp
INNER JOIN repo_tracks USING(repository_id, trackname)
GROUP BY effname, family
HAVING bool_and(coalesce(repo_tracks.end_ts = now(), FALSE))
UNION ALL
SELECT
	effname,
	1,
	family
FROM (
	SELECT
		effname,
		(SELECT id FROM repositories WHERE repositories.name = repo) AS repository_id,
		trackname,
		family
	FROM incoming_packages
	WHERE (SELECT state FROM repositories WHERE repositories.name = repo) = 'active'
) AS tmp
INNER JOIN repo_tracks USING(repository_id, trackname)
GROUP BY effname, family
HAVING bool_and(coalesce(repo_tracks.start_ts = now(), FALSE));
