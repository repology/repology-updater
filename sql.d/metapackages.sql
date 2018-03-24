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
-- !!get_metapackage_history(effname, limit=None) -> array of dicts
--
--------------------------------------------------------------------------------
SELECT
	now() - ts AS ago,
	type,
	data
FROM metapackages_events
WHERE effname = %(effname)s
ORDER BY ts DESC, type DESC
LIMIT %(limit)s;


--------------------------------------------------------------------------------
--
-- !!get_metapackages(effnames) -> dict of dicts
--
--------------------------------------------------------------------------------
SELECT
	effname,
	num_families,
	has_related
FROM metapackages
WHERE effname = ANY(%(effnames)s);

--------------------------------------------------------------------------------
--
-- !!query_metapackages(pivot=None, reverse=False, search=None, maintainer=None, inrepo=None, notinrepo=None, min_repos=None, max_repos=None, min_families=None, max_families=None, min_repos_newest=None, max_repos_newest=None, min_families_newest=None, max_families_newest=None, category=None, newest=False, outdated=False, problematic=False, has_related=False, limit=None) -> dict of dicts
--
--------------------------------------------------------------------------------
SELECT
	effname,
	num_families,
	has_related
FROM metapackages
WHERE
	(
		num_repos_nonshadow > 0
	{% if pivot %}
	) AND (
		-- pivot condition
		{% if reverse %}
		effname <= %(pivot)s
		{% else %}
		effname >= %(pivot)s
		{% endif %}
	{% endif %}
	{% if search %}
	) AND (
		-- search condition
		effname LIKE ('%%' || %(search)s || '%%')
	{% endif %}

	{% if min_repos is not none %}
	) AND (
		num_repos >= %(min_repos)s
	{% endif %}
	{% if max_repos is not none %}
	) AND (
		num_repos <= %(max_repos)s
	{% endif %}
	{% if min_families is not none %}
	) AND (
		num_families >= %(min_families)s
	{% endif %}
	{% if max_families is not none %}
	) AND (
		num_families <= %(max_families)s
	{% endif %}
	{% if min_repos_newest is not none %}
	) AND (
		num_repos_newest >= %(min_repos_newest)s
	{% endif %}
	{% if max_repos_newest is not none %}
	) AND (
		num_repos_newest <= %(max_repos_newest)s
	{% endif %}
	{% if min_families_newest is not none %}
	) AND (
		num_families_newest >= %(min_families_newest)s
	{% endif %}
	{% if max_families_newest is not none %}
	) AND (
		num_families_newest <= %(max_families_newest)s
	{% endif %}

	{% if has_related %}
	) AND (
		has_related
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
				{% if newest %}
				) AND (
					num_packages_newest > 0 OR num_packages_devel > 0
				{% endif %}
				{% if outdated %}
				) AND (
					num_packages_outdated > 0
				{% endif %}
				{% if problematic %}
				) AND (
					num_packages_ignored > 0 OR num_packages_incorrect > 0 OR num_packages_untrusted > 0
				{% endif %}
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
				{% if newest %}
				) AND (
					num_packages_newest > 0 OR num_packages_devel > 0
				{% endif %}
				{% if outdated %}
				) AND (
					num_packages_outdated > 0
				{% endif %}
				{% if problematic %}
				) AND (
					num_packages_ignored > 0 OR num_packages_incorrect > 0 OR num_packages_untrusted > 0
				{% endif %}
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
			WHERE num_packages_newest > 0 OR num_packages_devel > 0
		)
	{% endif %}
	{% if not maintainer and not repo and outdated %}
	) AND (
		-- outdated not handled for either maintainer or repo
		effname IN (
			SELECT
				effname
			FROM repo_metapackages
			WHERE num_packages_outdated > 0
		)
	{% endif %}
	{% if not maintainer and not repo and problematic %}
	) AND (
		-- problematic not handled for either maintainer or repo
		effname IN (
			SELECT
				effname
			FROM repo_metapackages
			WHERE num_packages_ignored > 0 OR num_packages_incorrect > 0 OR num_packages_untrusted > 0
		)
	{% endif %}
	)
ORDER BY
	effname{% if reverse %} DESC{% endif %}
LIMIT %(limit)s;


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
-- !!get_raising_metapackages1(limit=None) -> array of dicts
--
--------------------------------------------------------------------------------
SELECT
	effname,
	num_families,
	(num_families-1)/extract(epoch FROM now() - first_seen) * 60 * 60 * 24 * 7 AS rate
FROM metapackages
WHERE
	num_families > 1 AND first_seen != '2018-03-01 17:40:52.539797+03'
ORDER BY rate DESC, effname
LIMIT %(limit)s;


--------------------------------------------------------------------------------
--
-- !!get_raising_metapackages2(limit=None) -> array of dicts
--
--------------------------------------------------------------------------------
SELECT
	effname,
	num_families,
	(num_families-1)/extract(epoch FROM now() - first_seen) * 60 * 60 * 24 * 7 AS rate
FROM metapackages
WHERE
	num_families > 1 AND num_families < 4
ORDER BY rate DESC, effname
LIMIT %(limit)s;


--------------------------------------------------------------------------------
--
-- !!get_metapackage_families_count(effname) -> single value
--
--------------------------------------------------------------------------------
SELECT count(DISTINCT family) FROM packages WHERE effname = %(effname)s;


--------------------------------------------------------------------------------
--
-- !!get_metapackage_related_metapackages(effname, limit) -> dict of dicts
--
--------------------------------------------------------------------------------
SELECT
	effname,
	num_families,
	has_related
FROM metapackages
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
