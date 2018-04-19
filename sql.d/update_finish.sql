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
--------------------------------------------------------------------------------

--------------------------------------------------------------------------------
-- Extract urls
--------------------------------------------------------------------------------

DELETE
FROM url_relations;

INSERT
INTO url_relations
SELECT
	(SELECT id FROM metapackages WHERE effname = tmp.effname),
	url
FROM (
	SELECT DISTINCT
		effname,
		simplify_url(homepage) AS url
	FROM packages
	WHERE homepage ~ '^https?://'
) AS tmp;

ANALYZE url_relations;

--------------------------------------------------------------------------------
-- Update aggregate tables: metapackages
--------------------------------------------------------------------------------
INSERT
INTO metapackages (
	effname,
	num_repos,
	num_repos_nonshadow,
	num_families,
	num_repos_newest,
	num_families_newest,
	max_repos,
	max_families,
	first_seen,
	last_seen,

	devel_versions,
	devel_repos,
	devel_version_update,

	newest_versions,
	newest_repos,
	newest_version_update,

	all_repos
)
SELECT
	effname,
	count(DISTINCT repo),
	count(DISTINCT repo) FILTER (WHERE NOT shadow),
	count(DISTINCT family),
	count(DISTINCT repo) FILTER (WHERE versionclass = 1 OR versionclass = 5),
	count(DISTINCT family) FILTER (WHERE versionclass = 1 OR versionclass = 5),
	count(DISTINCT repo),
	count(DISTINCT family),
	now(),
	now(),

	-- XXX: technical dept warning: since we don't distinguish "newest unique" and "newest devel" statuses, we have
	-- to use flags here. Better solution should be implemented in future
	array_agg(DISTINCT version ORDER BY version) FILTER(WHERE versionclass = 5 OR (versionclass = 4 AND (flags & 2)::bool)),
	array_agg(DISTINCT repo ORDER BY repo) FILTER(WHERE versionclass = 5 OR (versionclass = 4 AND (flags & 2)::bool)),
	NULL,  -- first time we see this metapackage, time of version update is not known yet

	array_agg(DISTINCT version ORDER BY version) FILTER(WHERE versionclass = 1 OR (versionclass = 4 AND NOT (flags & 2)::bool)),
	array_agg(DISTINCT repo ORDER BY repo) FILTER(WHERE versionclass = 1 OR (versionclass = 4 AND NOT (flags & 2)::bool)),
	NULL,

	array_agg(DISTINCT repo ORDER BY repo)
FROM packages
GROUP BY effname
ON CONFLICT (effname)
DO UPDATE SET
	num_repos = EXCLUDED.num_repos,
	num_repos_nonshadow = EXCLUDED.num_repos_nonshadow,
	num_families = EXCLUDED.num_families,
	num_repos_newest = EXCLUDED.num_repos_newest,
	num_families_newest = EXCLUDED.num_families_newest,
	max_repos = greatest(metapackages.max_repos, EXCLUDED.num_repos),
	max_families = greatest(metapackages.max_families, EXCLUDED.num_families),
	last_seen = now(),

	devel_versions = EXCLUDED.devel_versions,
	devel_repos = EXCLUDED.devel_repos,
	devel_version_update =
		-- We want version update time to be as reliable as possible so
		-- the policy is that it's better to have no known last update time
		-- than to have an incorrect one.
		--
		-- For instance, we want to ignore addition of new repo which has
		-- the greated version than we know and don't record this as an
		-- update, because actual update could've happened long ago.
		CASE
			WHEN
				-- no change (both defined and equal)
				version_compare_simple(EXCLUDED.devel_versions[1], metapackages.devel_versions[1]) = 0
			THEN metapackages.devel_version_update
			WHEN
				-- trusted update (both should be defined)
				version_compare_simple(EXCLUDED.devel_versions[1], metapackages.devel_versions[1]) > 0 AND
				EXISTS (SELECT unnest(EXCLUDED.devel_repos) INTERSECT SELECT unnest(metapackages.all_repos))
			THEN now()
			ELSE NULL -- else reset
		END,

	newest_versions = EXCLUDED.newest_versions,
	newest_repos = EXCLUDED.newest_repos,
	newest_version_update =
		CASE
			WHEN
				-- no change (both defined and equal)
				version_compare_simple(EXCLUDED.newest_versions[1], metapackages.newest_versions[1]) = 0
			THEN metapackages.newest_version_update
			WHEN
				-- trusted update (both should be defined)
				version_compare_simple(EXCLUDED.newest_versions[1], metapackages.newest_versions[1]) > 0 AND
				EXISTS (SELECT unnest(EXCLUDED.newest_repos) INTERSECT SELECT unnest(metapackages.all_repos))
			THEN now()
			ELSE NULL -- else reset
		END,

	all_repos = EXCLUDED.all_repos;

-- related
UPDATE metapackages
SET
	has_related = EXISTS (
		SELECT *  -- returns other effnames for these urls
		FROM url_relations
		WHERE url IN (
			SELECT url  -- returns urls for this effname
			FROM url_relations
			WHERE metapackage_id = metapackages.id
		) AND metapackage_id != metapackages.id
	);

-- reset (XXX: this won't work well with partial updates)
UPDATE metapackages
SET
	num_repos = 0,
	num_repos_nonshadow = 0,
	num_families = 0,
	num_repos_newest = 0,
	num_families_newest = 0,
	has_related = false
WHERE
	last_seen != now();

--------------------------------------------------------------------------------
-- Update aggregate tables: maintainers
--------------------------------------------------------------------------------
INSERT
INTO maintainers (
	maintainer,

	num_packages,
	num_packages_newest,
	num_packages_outdated,
	num_packages_ignored,
	num_packages_unique,
	num_packages_devel,
	num_packages_legacy,
	num_packages_incorrect,
	num_packages_untrusted,
	num_packages_noscheme,
	num_packages_rolling,

	num_metapackages,
	num_metapackages_outdated,

	first_seen,
	last_seen
)
SELECT
	unnest(maintainers) AS maintainer,

	count(*),
	count(*) FILTER (WHERE versionclass = 1),
	count(*) FILTER (WHERE versionclass = 2),
	count(*) FILTER (WHERE versionclass = 3),
	count(*) FILTER (WHERE versionclass = 4),
	count(*) FILTER (WHERE versionclass = 5),
	count(*) FILTER (WHERE versionclass = 6),
	count(*) FILTER (WHERE versionclass = 7),
	count(*) FILTER (WHERE versionclass = 8),
	count(*) FILTER (WHERE versionclass = 9),
	count(*) FILTER (WHERE versionclass = 10),

	count(DISTINCT effname),
	count(DISTINCT effname) FILTER(WHERE versionclass = 2),

	now(),
	now()
FROM packages
GROUP BY maintainer
ON CONFLICT (maintainer)
DO UPDATE SET
	num_packages = EXCLUDED.num_packages,
	num_packages_newest = EXCLUDED.num_packages_newest,
	num_packages_outdated = EXCLUDED.num_packages_outdated,
	num_packages_ignored = EXCLUDED.num_packages_ignored,
	num_packages_unique = EXCLUDED.num_packages_unique,
	num_packages_devel = EXCLUDED.num_packages_devel,
	num_packages_legacy = EXCLUDED.num_packages_legacy,
	num_packages_incorrect = EXCLUDED.num_packages_incorrect,
	num_packages_untrusted = EXCLUDED.num_packages_untrusted,
	num_packages_noscheme = EXCLUDED.num_packages_noscheme,
	num_packages_rolling = EXCLUDED.num_packages_rolling,

	num_metapackages = EXCLUDED.num_metapackages,
	num_metapackages_outdated = EXCLUDED.num_metapackages_outdated,

	last_seen = now();

-- per-repo package counts
UPDATE maintainers
SET
	repository_package_counts = tmp.repository_package_counts,
	repository_metapackage_counts = tmp.repository_metapackage_counts
FROM (
	SELECT
		maintainer,
		json_object_agg(repo, numrepopkg) AS repository_package_counts,
		json_object_agg(repo, numrepometapkg) AS repository_metapackage_counts
	FROM (
		SELECT
			unnest(maintainers) AS maintainer,
			repo,
			count(*) AS numrepopkg,
			count(DISTINCT effname) AS numrepometapkg
		FROM packages
		GROUP BY maintainer, repo
	) AS sub
	GROUP BY maintainer
) AS tmp
WHERE maintainers.maintainer = tmp.maintainer;

-- per-category package counts
UPDATE maintainers
SET
	category_metapackage_counts = tmp.category_metapackage_counts
FROM (
	SELECT
		maintainer,
		json_object_agg(category, numcatmetapkg) AS category_metapackage_counts
	FROM (
		SELECT
			unnest(maintainers) AS maintainer,
			category,
			count(DISTINCT effname) AS numcatmetapkg
		FROM packages
		WHERE category IS NOT NULL
		GROUP BY maintainer, category
	) AS sub
	GROUP BY maintainer
) AS tmp
WHERE maintainers.maintainer = tmp.maintainer;

-- reset (XXX: this won't work well with partial updates)
UPDATE maintainers
SET
	num_packages = 0,
	num_packages_newest = 0,
	num_packages_outdated = 0,
	num_packages_ignored = 0,
	num_packages_unique = 0,
	num_packages_devel = 0,
	num_packages_legacy = 0,
	num_packages_incorrect = 0,
	num_packages_untrusted = 0,
	num_packages_noscheme = 0,
	num_packages_rolling = 0,
	num_metapackages = 0,
	num_metapackages_outdated = 0,

	repository_package_counts = '{}',
	repository_metapackage_counts = '{}',

	category_metapackage_counts = '{}'
WHERE
	last_seen != now();

--------------------------------------------------------------------------------
-- Update aggregate tables: repositories
--------------------------------------------------------------------------------
INSERT
INTO repositories (
	name,

	num_packages,
	num_packages_newest,
	num_packages_outdated,
	num_packages_ignored,
	num_packages_unique,
	num_packages_devel,
	num_packages_legacy,
	num_packages_incorrect,
	num_packages_untrusted,
	num_packages_noscheme,
	num_packages_rolling,

	num_metapackages,
	num_metapackages_unique,
	num_metapackages_newest,
	num_metapackages_outdated,
	num_metapackages_comparable,

	first_seen,
	last_seen
)
SELECT
	repo,

	sum(num_packages),
	sum(num_packages_newest),
	sum(num_packages_outdated),
	sum(num_packages_ignored),
	sum(num_packages_unique),
	sum(num_packages_devel),
	sum(num_packages_legacy),
	sum(num_packages_incorrect),
	sum(num_packages_untrusted),
	sum(num_packages_noscheme),
	sum(num_packages_rolling),

	count(*),
	count(*) FILTER (WHERE "unique"),
	count(*) FILTER (WHERE NOT "unique" AND (num_packages_newest > 0 OR num_packages_devel > 0) AND num_packages_outdated = 0),
	count(*) FILTER (WHERE num_packages_outdated > 0),
	count(*) FILTER (WHERE
		-- newest
		(NOT "unique" AND (num_packages_newest > 0 OR num_packages_devel > 0) AND num_packages_outdated = 0) OR
		-- outdated
		(num_packages_outdated > 0) OR
		-- problematic subset
		(num_packages_incorrect > 0)
	),

	now(),
	now()
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
		max(num_families) = 1 AS "unique"
	FROM packages INNER JOIN metapackages USING(effname)
	WHERE num_repos_nonshadow > 0
	GROUP BY effname, repo
) AS tmp
GROUP BY repo
ON CONFLICT (name)
DO UPDATE SET
	num_packages = EXCLUDED.num_packages,
	num_packages_newest = EXCLUDED.num_packages_newest,
	num_packages_outdated = EXCLUDED.num_packages_outdated,
	num_packages_ignored = EXCLUDED.num_packages_ignored,
	num_packages_unique = EXCLUDED.num_packages_unique,
	num_packages_devel = EXCLUDED.num_packages_devel,
	num_packages_legacy = EXCLUDED.num_packages_legacy,
	num_packages_incorrect = EXCLUDED.num_packages_incorrect,
	num_packages_untrusted = EXCLUDED.num_packages_untrusted,
	num_packages_noscheme = EXCLUDED.num_packages_noscheme,
	num_packages_rolling = EXCLUDED.num_packages_rolling,

	num_metapackages = EXCLUDED.num_metapackages,
	num_metapackages_unique = EXCLUDED.num_metapackages_unique,
	num_metapackages_newest = EXCLUDED.num_metapackages_newest,
	num_metapackages_outdated = EXCLUDED.num_metapackages_outdated,
	num_metapackages_comparable = EXCLUDED.num_metapackages_comparable,

	last_seen = now();

-- maintainer counts
UPDATE repositories
SET
	num_maintainers = (
		SELECT
			count(DISTINCT maintainer)
		FROM (
			SELECT
				unnest(maintainers) AS maintainer
			FROM packages
			WHERE repo = repositories.name
		) as TMP
	);

-- reset (XXX: this won't work well with partial updates)
UPDATE repositories
SET
	num_packages = 0,
	num_packages_newest = 0,
	num_packages_outdated = 0,
	num_packages_ignored = 0,
	num_packages_unique = 0,
	num_packages_devel = 0,
	num_packages_legacy = 0,
	num_packages_incorrect = 0,
	num_packages_untrusted = 0,
	num_packages_noscheme = 0,
	num_packages_rolling = 0,

	num_metapackages = 0,
	num_metapackages_unique = 0,
	num_metapackages_newest = 0,
	num_metapackages_outdated = 0,
	num_metapackages_comparable = 0,

	num_problems = 0,

	num_maintainers = 0
WHERE
	last_seen != now();

--------------------------------------------------------------------------------
-- Update binding tables
--------------------------------------------------------------------------------

-- per-repository
DELETE FROM repo_metapackages;

INSERT INTO repo_metapackages(
	repository_id,
	effname,

	newest,
	outdated,
	problematic,

	"unique"
)
SELECT
	(SELECT id FROM repositories WHERE name = repo),
	effname,

	count(*) FILTER (WHERE versionclass = 1 OR versionclass = 4 OR versionclass = 5) > 0,
	count(*) FILTER (WHERE versionclass = 2) > 0,
	count(*) FILTER (WHERE versionclass = 3 OR versionclass = 7 OR versionclass = 8) > 0,

	max(num_families) = 1
FROM packages INNER JOIN metapackages USING(effname)
WHERE num_repos_nonshadow > 0
GROUP BY effname, repo;

-- per-category
DELETE FROM category_metapackages;

INSERT INTO category_metapackages (
	category,
	effname,
	"unique"
)
SELECT
	category,
	effname,
	max(num_families) = 1
FROM packages INNER JOIN metapackages USING(effname)
WHERE category IS NOT NULL AND num_repos_nonshadow > 0
GROUP BY effname, category;

-- per-maintainer
DELETE FROM maintainer_metapackages;

INSERT INTO maintainer_metapackages (
	maintainer_id,
	effname,

	newest,
	outdated,
	problematic
)
SELECT
	(SELECT id FROM maintainers WHERE maintainer = tmp.maintainer),
	effname,

	newest,
	outdated,
	problematic
FROM
(
	SELECT
		unnest(maintainers) AS maintainer,
		effname,
		count(*) FILTER (WHERE versionclass = 1 OR versionclass = 4 OR versionclass = 5) > 0 AS newest,
		count(*) FILTER (WHERE versionclass = 2) > 0 AS outdated,
		count(*) FILTER (WHERE versionclass = 3 OR versionclass = 7 OR versionclass = 8) > 0 AS problematic
	FROM packages
	GROUP BY unnest(maintainers), effname
) AS tmp;

--------------------------------------------------------------------------------
-- Update problems
--------------------------------------------------------------------------------

-- pre-cleanup
DELETE
FROM problems;

-- add different kinds of problems
INSERT INTO problems (
	package_id,
	repo,
	name,
	effname,
	maintainer,
	problem
)
SELECT DISTINCT
	packages.id,
	packages.repo,
	packages.name,
	packages.effname,
	unnest(CASE WHEN packages.maintainers = '{}' THEN '{null}' ELSE packages.maintainers END),
	'Homepage link "' ||
		links.url ||
		'" is dead (' ||
		CASE
			WHEN links.status=-1 THEN 'connect timeout'
			WHEN links.status=-2 THEN 'too many redirects'
			WHEN links.status=-4 THEN 'cannot connect'
			WHEN links.status=-5 THEN 'invalid url'
			WHEN links.status=-6 THEN 'DNS problem'
			ELSE 'HTTP error ' || links.status
		END ||
		') for more than a month.'
FROM packages
INNER JOIN links ON (packages.homepage = links.url)
WHERE
	(links.status IN (-1, -2, -4, -5, -6, 400, 404) OR links.status >= 500) AND
	(
		(links.last_success IS NULL AND links.first_extracted < now() - INTERVAL '30' DAY) OR
		links.last_success < now() - INTERVAL '30' DAY
	);

INSERT INTO problems (
	package_id,
	repo,
	name,
	effname,
	maintainer,
	problem
)
SELECT DISTINCT
	packages.id,
	packages.repo,
	packages.name,
	packages.effname,
	unnest(CASE WHEN packages.maintainers = '{}' THEN '{null}' ELSE packages.maintainers END),
	'Homepage link "' ||
		links.url ||
		'" is a permanent redirect to "' ||
		links.location ||
		'" and should be updated'
FROM packages
INNER JOIN links ON (packages.homepage = links.url)
WHERE
	links.redirect = 301 AND
	replace(links.url, 'http://', 'https://') = links.location;

INSERT INTO problems(package_id, repo, name, effname, maintainer, problem)
SELECT DISTINCT
	id,
	repo,
	name,
	effname,
	unnest(CASE WHEN packages.maintainers = '{}' THEN '{null}' ELSE packages.maintainers END),
	'Homepage link "' || homepage || '" points to Google Code which was discontinued. The link should be updated (probably along with download URLs). If this link is still alive, it may point to a new project homepage.'
FROM packages
WHERE
	homepage SIMILAR TO 'https?://([^/]+.)?googlecode.com(/%%)?' OR
	homepage SIMILAR TO 'https?://code.google.com(/%%)?';

INSERT INTO problems(package_id, repo, name, effname, maintainer, problem)
SELECT DISTINCT
	id,
	repo,
	name,
	effname,
	unnest(CASE WHEN packages.maintainers = '{}' THEN '{null}' ELSE packages.maintainers END),
	'Homepage link "' || homepage || '" points to codeplex which was discontinued. The link should be updated (probably along with download URLs).'
FROM packages
WHERE
	homepage SIMILAR TO 'https?://([^/]+.)?codeplex.com(/%%)?';

INSERT INTO problems(package_id, repo, name, effname, maintainer, problem)
SELECT DISTINCT
	id,
	repo,
	name,
	effname,
	unnest(CASE WHEN packages.maintainers = '{}' THEN '{null}' ELSE packages.maintainers END),
	'Homepage link "' || homepage || '" points to Gna which was discontinued. The link should be updated (probably along with download URLs).'
FROM packages
WHERE
	homepage SIMILAR TO 'https?://([^/]+.)?gna.org(/%%)?';

-- update per-repository problem counts
UPDATE repositories
SET
	num_problems = (SELECT count(DISTINCT effname) FROM problems WHERE repo = repositories.name);

--------------------------------------------------------------------------------
-- Update links
--------------------------------------------------------------------------------

-- cleanup stale
DELETE FROM links
WHERE last_extracted < now() - INTERVAL '1' MONTH;

-- extract fresh
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

--------------------------------------------------------------------------------
-- Update global statistics
--------------------------------------------------------------------------------
UPDATE statistics SET
	num_packages = (SELECT count(*) FROM packages),
	num_metapackages = (SELECT count(*) FROM metapackages WHERE num_repos_nonshadow > 0),
	num_problems = (SELECT count(*) FROM problems),
	num_maintainers = (SELECT count(*) FROM maintainers);

--------------------------------------------------------------------------------
-- History snapshot
--------------------------------------------------------------------------------

-- per-repository counters
INSERT INTO repositories_history (
	ts,
	snapshot
)
SELECT
	now(),
	jsonb_object_agg(snapshot.name, to_jsonb(snapshot) - 'name')
FROM (
	SELECT
		name,
		num_metapackages,
		num_metapackages_unique,
		num_metapackages_newest,
		num_metapackages_outdated,
		num_metapackages_comparable,
		num_problems,
		num_maintainers
	FROM repositories
) AS snapshot;

-- global statistics
INSERT INTO statistics_history (
	ts,
	snapshot
)
SELECT
	now(),
	to_jsonb(snapshot)
FROM (
	SELECT
		*
	FROM statistics
) AS snapshot;
