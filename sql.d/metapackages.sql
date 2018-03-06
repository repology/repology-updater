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
-- !!query_metapackages(pivot=None, reverse=False, search=None, maintainer=None, inrepo=None, notinrepo=None, minspread=None, maxspread=None, category=None, newest=False, outdated=False, newest_single_repo=False, newest_single_family=False, problematic=False, limit=None, fields=None) -> array of packages
--
--------------------------------------------------------------------------------
SELECT
{% if fields %}
	{{ fields | join(',') }}
{% else %}
	*
{% endif %}
FROM packages
WHERE effname IN (
	SELECT effname
	FROM metapackages
	WHERE
		(
			num_repos_nonshadow > 0
{% if pivot %}
		) AND (
			-- pivot condition
			(NOT %(reverse)s AND effname >= %(pivot)s) OR
			(%(reverse)s AND effname <= %(pivot)s)
{% endif %}
{% if search %}
		) AND (
			-- search condition
			effname LIKE ('%%' || %(search)s || '%%')
{% endif %}
{% if minspread is not none %}
		) AND (
			-- spread conditions
			num_families >= %(minspread)s
{% endif %}
{% if maxspread is not none %}
		) AND (
			num_families <= %(maxspread)s
{% endif %}
{% if newest_single_repo %}
		) AND (
			-- single newest conditions
			num_repos_newest = 1
{% endif %}
{% if newest_single_family %}
		) AND (
			num_families_newest = 1
{% endif %}
{% if inrepo %}
		) AND (
			-- in repo condition
			effname IN (
				SELECT
					effname
				FROM repo_metapackages
				WHERE
					(
						repo = %(inrepo)s
					) AND (
						NOT %(newest)s OR
						num_packages_newest > 0 OR
						num_packages_devel > 0
					) AND (
						NOT %(outdated)s OR
						num_packages_outdated > 0
					) AND (
						NOT %(problematic)s OR
						num_packages_ignored > 0 OR
						num_packages_incorrect > 0 OR
						num_packages_untrusted > 0
					)
			)
{% endif %}
{% if notinrepo %}
		) AND (
			-- not in repo condition
			effname IN (
				SELECT
					effname
				FROM repo_metapackages
				GROUP BY effname
				HAVING count(*) FILTER (WHERE repo = %(notinrepo)s) = 0
			)
{% endif %}
{% if maintainer %}
		) AND (
			-- maintainer condition
			effname IN (
				SELECT
					effname
				FROM maintainer_metapackages
				WHERE
					(
						maintainer = %(maintainer)s
					) AND (
						NOT %(newest)s OR
						num_packages_newest > 0 OR
						num_packages_devel > 0
					) AND (
						NOT %(outdated)s OR
						num_packages_outdated > 0
					) AND (
						NOT %(problematic)s OR
						num_packages_ignored > 0 OR
						num_packages_incorrect > 0 OR
						num_packages_untrusted > 0
					)
			)
{% endif %}
{% if category %}
		) AND (
			-- category condition
			effname IN (
				SELECT
					effname
				FROM category_metapackages
				WHERE category = %(category)s
			)
{% endif %}
{% if not maintainer and not repo and newest %}
		) AND (
			-- newest not handled for either maintainer or repo
			effname IN (
				SELECT
					effname
				FROM repo_metapackages
				WHERE
					(
						num_packages_newest > 0 OR
						num_packages_devel > 0
					)
			)
{% endif %}
{% if not maintainer and not repo and outdated %}
		) AND (
			-- outdated not handled for either maintainer or repo
			effname IN (
				SELECT
					effname
				FROM repo_metapackages
				WHERE
					(
						num_packages_outdated > 0
					)
			)
{% endif %}
{% if not maintainer and not repo and problematic %}
		) AND (
			-- problematic not handled for either maintainer or repo
			effname IN (
				SELECT
					effname
				FROM repo_metapackages
				WHERE
					(
						num_packages_ignored > 0 OR
						num_packages_incorrect > 0 OR
						num_packages_untrusted > 0
					)
			)
{% endif %}
		)
	ORDER BY
		CASE WHEN NOT %(reverse)s THEN effname ELSE NULL END,
		CASE WHEN %(reverse)s THEN effname ELSE NULL END DESC
	LIMIT %(limit)s
);


--------------------------------------------------------------------------------
--
-- !!get_recently_added_metapackages(limit=None) -> array of dicts
--
--------------------------------------------------------------------------------
SELECT
	now() - first_seen AS ago,
	effname,
	has_related
FROM metapackages
WHERE num_repos_nonshadow > 0
ORDER BY first_seen DESC, effname
LIMIT %(limit)s;


--------------------------------------------------------------------------------
--
-- !!get_recently_removed_metapackages(limit=None) -> array of dicts
--
--------------------------------------------------------------------------------
SELECT
	now() - last_seen AS ago,
	effname
FROM metapackages
WHERE num_repos = 0
ORDER BY last_seen DESC, effname
LIMIT %(limit)s;


--------------------------------------------------------------------------------
--
-- !!get_metapackage_packages(effname, fields=None) -> array of packages
--
--------------------------------------------------------------------------------
SELECT
{% if fields %}
	{{ fields | join(',') }}
{% else %}
	*
{% endif %}
FROM packages
WHERE effname = %(effname)s;


--------------------------------------------------------------------------------
--
-- !!get_metapackage_families_count(effname) -> single value
--
--------------------------------------------------------------------------------
SELECT count(DISTINCT family) FROM packages WHERE effname = %(effname)s;


--------------------------------------------------------------------------------
--
-- !!get_metapackages_packages(effnames, fields=None) -> array of packages
--
--------------------------------------------------------------------------------
SELECT
{% if fields %}
	{{ fields | join(',') }}
{% else %}
	*
{% endif %}
FROM packages
WHERE effname = ANY(%(effnames)s);


--------------------------------------------------------------------------------
--
-- !!get_metapackage_related_metapackages(effname, limit, fields=None) -> array of packages
--
--------------------------------------------------------------------------------
SELECT
{% if fields %}
	{{ fields | join(',') }}
{% else %}
	*
{% endif %}
FROM packages
WHERE effname IN (
	WITH RECURSIVE r AS (
		SELECT
			effname,
			url
		FROM url_relations
		WHERE effname = %(effname)s
		UNION
		SELECT
			url_relations.effname,
			url_relations.url
		FROM url_relations
		JOIN r ON
			url_relations.effname = r.effname OR url_relations.url = r.url
	)
	SELECT DISTINCT
		effname
	FROM r
	ORDER BY effname
	LIMIT %(limit)s
);


--------------------------------------------------------------------------------
--
-- !!get_all_metapackage_names_by_min_spread_count(spread) -> single value
--
--------------------------------------------------------------------------------
SELECT
	count(DISTINCT effname)
FROM metapackages
WHERE num_repos_nonshadow > 0 AND num_families >= %(spread)s;


--------------------------------------------------------------------------------
--
-- !!get_all_metapackage_names_by_min_spread(spread, limit=None) -> array of values
--
--------------------------------------------------------------------------------
SELECT DISTINCT
	effname
FROM metapackages
WHERE num_repos_nonshadow > 0 AND num_families >= %(spread)s
LIMIT %(limit)s;


--------------------------------------------------------------------------------
--
-- !!get_all_metapackage_names_by_spread(spread, limit=None) -> array of values
--
--------------------------------------------------------------------------------
SELECT DISTINCT
	effname
FROM metapackages
WHERE num_repos_nonshadow > 0 AND num_families = %(spread)s
LIMIT %(limit)s;


--------------------------------------------------------------------------------
--
-- !!add_packages(many packages)
--
--------------------------------------------------------------------------------
INSERT INTO packages(
	repo,
	family,
	subrepo,

	name,
	effname,

	version,
	origversion,
	versionclass,

	maintainers,
	category,
	comment,
	homepage,
	licenses,
	downloads,

	flags,
	shadow,
	verfixed,

	flavors,

	extrafields
) VALUES (
	%(repo)s,
	%(family)s,
	%(subrepo)s,

	%(name)s,
	%(effname)s,

	%(version)s,
	%(origversion)s,
	%(versionclass)s,

	%(maintainers)s,
	%(category)s,
	%(comment)s,
	%(homepage)s,
	%(licenses)s,
	%(downloads)s,

	%(flags)s,
	%(shadow)s,
	%(verfixed)s,

	%(flavors)s,

	%(extrafields)s
)
