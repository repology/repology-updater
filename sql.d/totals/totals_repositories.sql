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
WITH expected AS (
	SELECT
		repo AS name,

		sum(num_packages) AS num_packages,
		sum(num_packages_newest) AS num_packages_newest,
		sum(num_packages_outdated) AS num_packages_outdated,
		sum(num_packages_ignored) AS num_packages_ignored,
		sum(num_packages_unique) AS num_packages_unique,
		sum(num_packages_devel) AS num_packages_devel,
		sum(num_packages_legacy) AS num_packages_legacy,
		sum(num_packages_incorrect) AS num_packages_incorrect,
		sum(num_packages_untrusted) AS num_packages_untrusted,
		sum(num_packages_noscheme) AS num_packages_noscheme,
		sum(num_packages_rolling) AS num_packages_rolling,
		sum(num_packages_vulnerable) AS num_packages_vulnerable,

		count(*) AS num_metapackages,
		count(*) FILTER (WHERE "unique") AS num_metapackages_unique,
		count(*) FILTER (WHERE NOT "unique" AND (num_packages_newest > 0 OR num_packages_devel > 0) AND num_packages_outdated = 0) AS num_metapackages_newest,
		count(*) FILTER (WHERE num_packages_outdated > 0) AS num_metapackages_outdated,
		count(*) FILTER (WHERE
			-- newest
			(NOT "unique" AND (num_packages_newest > 0 OR num_packages_devel > 0) AND num_packages_outdated = 0) OR
			-- outdated
			(num_packages_outdated > 0) OR
			-- problematic subset
			(num_packages_incorrect > 0)
		) AS num_metapackages_comparable,
		count(*) FILTER (WHERE
			num_packages_ignored > 0 OR
			num_packages_incorrect > 0 OR
			num_packages_untrusted > 0
		) AS num_metapackages_problematic,
		count(*) FILTER (WHERE num_packages_vulnerable > 0) AS num_metapackages_vulnerable
	FROM (
		SELECT
			repo,
			effname,
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
			count(*) FILTER (WHERE (flags & (1 << 16))::boolean) AS num_packages_vulnerable,
			max(num_families) = 1 AS "unique"
		FROM packages INNER JOIN metapackages USING(effname)
		WHERE num_repos_nonshadow > 0
		GROUP BY effname, repo
	) AS tmp1
	GROUP BY repo
)
{% if do_fix %}
-- note: these changes are not shown to SELECT below due to how CTE work
, fix AS (
	UPDATE repositories
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
		num_packages_vulnerable = expected.num_packages_vulnerable,

		num_metapackages = expected.num_metapackages,
		num_metapackages_unique = expected.num_metapackages_unique,
		num_metapackages_newest = expected.num_metapackages_newest,
		num_metapackages_outdated = expected.num_metapackages_outdated,
		num_metapackages_comparable = expected.num_metapackages_comparable,
		num_metapackages_problematic = expected.num_metapackages_problematic,
		num_metapackages_vulnerable = expected.num_metapackages_vulnerable
	FROM expected
	WHERE repositories.name = expected.name
)
{% endif %}
SELECT
	name AS key,
	row_to_json(actual) AS actual,
	row_to_json(expected) AS expected
FROM
	expected FULL OUTER JOIN repositories actual using(name)
WHERE
	actual.name IS NULL OR

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
	actual.num_packages_vulnerable != coalesce(expected.num_packages_vulnerable, 0) OR

	actual.num_metapackages != coalesce(expected.num_metapackages, 0) OR
	actual.num_metapackages_unique != coalesce(expected.num_metapackages_unique, 0) OR
	actual.num_metapackages_newest != coalesce(expected.num_metapackages_newest, 0) OR
	actual.num_metapackages_outdated != coalesce(expected.num_metapackages_outdated, 0) OR
	actual.num_metapackages_comparable != coalesce(expected.num_metapackages_comparable, 0) OR
	actual.num_metapackages_problematic != coalesce(expected.num_metapackages_problematic, 0) OR
	actual.num_metapackages_vulnerable != coalesce(expected.num_metapackages_vulnerable, 0)
;
