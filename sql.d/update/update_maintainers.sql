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

--------------------------------------------------------------------------------
-- Update aggregate tables: maintainers, pass2, depends on repositories
--------------------------------------------------------------------------------
UPDATE maintainers
SET
	num_packages_per_repo = tmp.num_packages_per_repo,
	num_projects_per_repo = tmp.num_projects_per_repo,
	num_projects_newest_per_repo = tmp.num_projects_newest_per_repo,
	num_projects_outdated_per_repo = tmp.num_projects_outdated_per_repo,
	num_projects_problematic_per_repo = tmp.num_projects_problematic_per_repo,
	counts_per_repo = tmp.counts_per_repo,
	num_repos = tmp.num_repos
FROM (
	SELECT
		maintainer,
		json_object_agg(repo, num_packages) AS num_packages_per_repo,
		json_object_agg(repo, num_projects) AS num_projects_per_repo,
		json_object_agg(repo, num_projects_newest) AS num_projects_newest_per_repo,
		json_object_agg(repo, num_projects_outdated) AS num_projects_outdated_per_repo,
		json_object_agg(repo, num_projects_problematic) AS num_projects_problematic_per_repo,
		json_object_agg(repo,
			json_build_array(
				num_packages,
				num_projects,
				num_projects_newest,
				num_projects_outdated,
				num_projects_problematic
			)
		) AS counts_per_repo,
		count(DISTINCT repo) AS num_repos
	FROM (
		SELECT
			unnest(maintainers) AS maintainer,
			repo,
			count(*) AS num_packages,
			count(DISTINCT effname) AS num_projects,
			count(DISTINCT effname) FILTER (WHERE versionclass = 1 OR versionclass = 4 OR versionclass = 5) AS num_projects_newest,
			count(DISTINCT effname) FILTER (WHERE versionclass = 2) AS num_projects_outdated,
			count(DISTINCT effname) FILTER (WHERE versionclass = 3 OR versionclass = 7 OR versionclass = 8) AS num_projects_problematic
		FROM packages
		GROUP BY maintainer, repo
	) AS maintainer_repos
	GROUP BY maintainer
) AS tmp
WHERE maintainers.maintainer = tmp.maintainer;

UPDATE maintainers
SET
	num_packages_per_repo = '{}',

	num_projects_per_repo = '{}',
	num_projects_newest_per_repo = '{}',
	num_projects_outdated_per_repo = '{}',
	num_projects_problematic_per_repo = '{}',

	counts_per_repo = '{}',

	num_repos = 0
WHERE
	num_packages = 0;

ANALYZE maintainers;
