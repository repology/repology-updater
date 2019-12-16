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
-- Update binding tables: per-maintainer+repository
--------------------------------------------------------------------------------
DELETE FROM maintainer_and_repo_metapackages;

--- XXX: don't mix up with maintainer_repo_metapackages table update from update_post
INSERT INTO maintainer_and_repo_metapackages (
	maintainer_id,
	repository_id,
	effname,

	newest,
	outdated,
	problematic
)
SELECT
	(SELECT id FROM maintainers WHERE maintainer = tmp.maintainer),
	(SELECT id FROM repositories WHERE name = tmp.repo),
	effname,

	newest,
	outdated,
	problematic
FROM
(
	SELECT
		unnest(maintainers) AS maintainer,
		repo,
		effname,
		count(*) FILTER (WHERE versionclass = 1 OR versionclass = 4 OR versionclass = 5) > 0 AS newest,
		count(*) FILTER (WHERE versionclass = 2) > 0 AS outdated,
		count(*) FILTER (WHERE versionclass = 3 OR versionclass = 7 OR versionclass = 8) > 0 AS problematic
	FROM packages
	GROUP BY unnest(maintainers), repo, effname
) AS tmp
INNER JOIN metapackages USING(effname)
WHERE num_repos_nonshadow > 0;

ANALYZE maintainer_and_repo_metapackages;
