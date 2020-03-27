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
-- @param do_fix=False
-- @returns array of dicts
--------------------------------------------------------------------------------
WITH expected_alive AS (
	SELECT
		*
	FROM
	(
		SELECT
			unnest(maintainers) AS maintainer,

			count(*) AS num_packages,
			count(*) FILTER (WHERE versionclass = 1) AS num_packages_newest,
			count(*) FILTER (WHERE versionclass = 2) AS num_packages_outdated,
			count(*) FILTER (WHERE versionclass = 3) AS num_packages_ignored,
			count(*) FILTER (WHERE versionclass = 4) AS num_packages_unique,
			count(*) FILTER (WHERE versionclass = 5) AS num_packages_devel,
			count(*) FILTER (WHERE versionclass = 6) AS num_packages_legacy,
			count(*) FILTER (WHERE versionclass = 7) AS num_packages_incorrect,
			count(*) FILTER (WHERE versionclass = 8) AS num_packages_untrusted,
			count(*) FILTER (WHERE versionclass = 9) AS num_packages_noscheme,
			count(*) FILTER (WHERE versionclass = 10) AS num_packages_rolling,

			count(DISTINCT effname) AS num_projects,
			count(DISTINCT effname) FILTER(WHERE versionclass = 1 OR versionclass = 4 OR versionclass = 5) AS num_projects_newest,
			count(DISTINCT effname) FILTER(WHERE versionclass = 2) AS num_projects_outdated,
			count(DISTINCT effname) FILTER(WHERE versionclass = 3 OR versionclass = 7 OR versionclass = 8) AS num_projects_problematic
		FROM packages
		GROUP BY maintainer
	) AS plain INNER JOIN (
		SELECT
			maintainer,
			jsonb_object_agg(repo,
				jsonb_build_array(
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
		) AS by_repo_inner
		GROUP BY maintainer
	) AS by_repo USING (maintainer) LEFT OUTER JOIN (
		SELECT
			maintainer,
			jsonb_object_agg(category, num_projects) AS num_projects_per_category
		FROM (
			SELECT
				unnest(maintainers) AS maintainer,
				category,
				count(DISTINCT effname) AS num_projects
			FROM packages
			WHERE category IS NOT NULL
			GROUP BY maintainer, category
		) AS by_category_inner
		GROUP BY maintainer
	) AS by_category USING (maintainer)
), expected AS (
		SELECT
			*
		FROM expected_alive
	UNION ALL
		SELECT
			maintainer,

			0 AS num_packages,
			0 AS num_packages_newest,
			0 AS num_packages_outdated,
			0 AS num_packages_ignored,
			0 AS num_packages_unique,
			0 AS num_packages_devel,
			0 AS num_packages_legacy,
			0 AS num_packages_incorrect,
			0 AS num_packages_untrusted,
			0 AS num_packages_noscheme,
			0 AS num_packages_rolling,

			0 AS num_projects,
			0 AS num_projects_newest,
			0 AS num_projects_outdated,
			0 AS num_projects_problematic,

			NULL::jsonb AS counts_per_repo,

			0 AS num_repos,

			NULL::jsonb AS num_projects_per_category
		FROM maintainers
		WHERE NOT EXISTS (SELECT * FROM expected_alive WHERE expected_alive.maintainer = maintainers.maintainer)
)
{% if do_fix %}
-- note: these changes are not shown to SELECT below due to how CTE work
, fix AS (
	UPDATE maintainers
	SET
		num_packages = expected.num_packages,
		num_packages_newest = expected.num_packages_newest,
		num_packages_outdated = expected.num_packages_outdated,
		num_packages_ignored = expected.num_packages_ignored,
		num_packages_unique = expected.num_packages_unique,
		num_packages_devel = expected.num_packages_devel,
		num_packages_legacy = expected.num_packages_legacy,
		num_packages_incorrect = expected.num_packages_incorrect,
		num_packages_untrusted = expected.num_packages_untrusted,
		num_packages_noscheme = expected.num_packages_noscheme,
		num_packages_rolling = expected.num_packages_rolling,

		num_projects = expected.num_projects,
		num_projects_newest = expected.num_projects_newest,
		num_projects_outdated = expected.num_projects_outdated,
		num_projects_problematic = expected.num_projects_problematic,

		counts_per_repo = expected.counts_per_repo,

		num_projects_per_category = expected.num_projects_per_category,

		num_repos = expected.num_repos
	FROM expected
	WHERE maintainers.maintainer = expected.maintainer
)
{% endif %}
SELECT
	maintainer AS name,
	row_to_json(actual) AS actual,
	row_to_json(expected) AS expected
FROM
	expected FULL OUTER JOIN maintainers actual USING(maintainer)
WHERE
	actual.maintainer IS NULL OR

	actual.num_packages != coalesce(expected.num_packages, 0) OR
	actual.num_packages_newest != coalesce(expected.num_packages_newest, 0) OR
	actual.num_packages_outdated != coalesce(expected.num_packages_outdated, 0) OR
	actual.num_packages_ignored != coalesce(expected.num_packages_ignored, 0) OR
	actual.num_packages_unique != coalesce(expected.num_packages_unique, 0) OR
	actual.num_packages_devel != coalesce(expected.num_packages_devel, 0) OR
	actual.num_packages_legacy != coalesce(expected.num_packages_legacy, 0) OR
	actual.num_packages_incorrect != coalesce(expected.num_packages_incorrect, 0) OR
	actual.num_packages_untrusted != coalesce(expected.num_packages_untrusted, 0) OR
	actual.num_packages_noscheme != coalesce(expected.num_packages_noscheme, 0) OR
	actual.num_packages_rolling != coalesce(expected.num_packages_rolling, 0) OR

	actual.num_projects != coalesce(expected.num_projects, 0) OR
	actual.num_projects_newest != coalesce(expected.num_projects_newest, 0) OR
	actual.num_projects_outdated != coalesce(expected.num_projects_outdated, 0) OR
	actual.num_projects_problematic != coalesce(expected.num_projects_problematic, 0) OR

	actual.counts_per_repo IS DISTINCT FROM expected.counts_per_repo OR
	actual.num_projects_per_category IS DISTINCT FROM expected.num_projects_per_category OR

	actual.num_repos != coalesce(expected.num_repos, 0);
;
