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

SET SESSION work_mem = '128MB';

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
				EXCLUDED.devel_repos && metapackages.all_repos
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
				EXCLUDED.newest_repos && metapackages.all_repos
			THEN now()
			ELSE NULL -- else reset
		END,

	all_repos = EXCLUDED.all_repos;

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
UPDATE repositories
SET
	num_packages = tmp.num_packages,
	num_packages_newest = tmp.num_packages_newest,
	num_packages_outdated = tmp.num_packages_outdated,
	num_packages_ignored = tmp.num_packages_ignored,
	num_packages_unique = tmp.num_packages_unique,
	num_packages_devel = tmp.num_packages_devel,
	num_packages_legacy = tmp.num_packages_legacy,
	num_packages_incorrect = tmp.num_packages_incorrect,
	num_packages_untrusted = tmp.num_packages_untrusted,
	num_packages_noscheme = tmp.num_packages_noscheme,
	num_packages_rolling = tmp.num_packages_rolling,

	num_metapackages = tmp.num_metapackages,
	num_metapackages_unique = tmp.num_metapackages_unique,
	num_metapackages_newest = tmp.num_metapackages_newest,
	num_metapackages_outdated = tmp.num_metapackages_outdated,
	num_metapackages_comparable = tmp.num_metapackages_comparable,
	num_metapackages_problematic = tmp.num_metapackages_problematic,

	last_seen = now()
FROM (
	SELECT
		repo,

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
		) AS num_metapackages_problematic
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
	) AS tmp1
	GROUP BY repo
) AS tmp
WHERE name = tmp.repo;

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
	num_metapackages_problematic = 0,

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

ANALYZE repo_metapackages;

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

ANALYZE category_metapackages;

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

ANALYZE maintainer_metapackages;

--------------------------------------------------------------------------------
-- Update related urls
--------------------------------------------------------------------------------
DELETE
FROM url_relations;

INSERT
INTO url_relations
SELECT
	metapackage_id,
	urlhash
FROM
(
	SELECT
		metapackage_id,
		urlhash,
		count(*) OVER (PARTITION BY urlhash) AS metapackages_for_url
	FROM
	(
		SELECT DISTINCT
			(SELECT id FROM metapackages WHERE metapackages.effname = packages.effname) AS metapackage_id,
			(
				'x' || left(
					md5(
						simplify_url(homepage)
					), 16
				)
			)::bit(64)::bigint AS urlhash
		FROM packages
		WHERE homepage ~ '^https?://'
	) AS tmp2
) AS tmp1
WHERE metapackages_for_url > 1;

ANALYZE url_relations;

-- update flags for metapackages
UPDATE metapackages
SET
	has_related = EXISTS (
		SELECT *  -- returns other effnames for these urls
		FROM url_relations
		WHERE urlhash IN (
			SELECT urlhash  -- returns urls for this effname
			FROM url_relations
			WHERE metapackage_id = metapackages.id
		) AND metapackage_id != metapackages.id
	);

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
			WHEN links.ipv4_status_code=-1 THEN 'unknown error'
			WHEN links.ipv4_status_code=-100 THEN 'connect timeout'
			WHEN links.ipv4_status_code=-101 THEN 'invalid url'
			WHEN links.ipv4_status_code=-200 THEN 'unknown DNS problem'
			WHEN links.ipv4_status_code=-201 THEN 'domain not found'
			WHEN links.ipv4_status_code=-202 THEN 'no address record'
			WHEN links.ipv4_status_code=-203 THEN 'could not contact DNS servers'
			WHEN links.ipv4_status_code=-204 THEN 'DNS timeout'
			WHEN links.ipv4_status_code=-300 THEN 'connection refused'
			WHEN links.ipv4_status_code=-301 THEN 'no route to host'
			WHEN links.ipv4_status_code=-302 THEN 'connection reset by peer'
			WHEN links.ipv4_status_code=-303 THEN 'network unreackable'
			WHEN links.ipv4_status_code=-304 THEN 'server disconnected'
			WHEN links.ipv4_status_code=-306 THEN 'connection aborted'
			WHEN links.ipv4_status_code=-307 THEN 'address not available'
			WHEN links.ipv4_status_code=-400 THEN 'too many redirects'
			WHEN links.ipv4_status_code=-401 THEN 'SSL problem' -- XXX: legacy
			WHEN links.ipv4_status_code=-402 THEN 'HTTP protocol error'
			WHEN links.ipv4_status_code=-500 THEN 'SSL problem'
			WHEN links.ipv4_status_code=-501 THEN 'SSL certificate has expired'
			WHEN links.ipv4_status_code=-502 THEN 'SSL certificate issued for different hostname'
			WHEN links.ipv4_status_code=-503 THEN 'SSL self signed certificate'
			WHEN links.ipv4_status_code=-504 THEN 'SSL self signed certificate in chain'
			WHEN links.ipv4_status_code=-505 THEN 'SSL incomplete certificate chain'
			ELSE 'HTTP error ' || links.ipv4_status_code
		END ||
		') for more than a month.'
FROM packages
INNER JOIN links ON (packages.homepage = links.url)
WHERE
	NOT links.ipv4_success AND
	(
		links.ipv4_status_code < 0 OR
		links.ipv4_status_code >= 500 OR
		links.ipv4_status_code IN (400, 404)
	) AND
	(
		(links.ipv4_last_success IS NULL AND links.first_extracted < now() - INTERVAL '30' DAY) OR
		links.ipv4_last_success < now() - INTERVAL '30' DAY
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
		links.ipv4_permanent_redirect_target ||
		'" and should be updated'
FROM packages
INNER JOIN links ON (packages.homepage = links.url)
WHERE
	replace(links.url, 'http://', 'https://') = links.ipv4_permanent_redirect_target;

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

INSERT INTO problems(package_id, repo, name, effname, maintainer, problem)
SELECT DISTINCT
	id,
	repo,
	name,
	effname,
	unnest(CASE WHEN packages.maintainers = '{}' THEN '{null}' ELSE packages.maintainers END),
	'Homepage link "' || homepage || '" points to CPAN which was discontinued. The link should be updated to https://metacpan.org (probably along with download URLs). See https://www.perl.com/article/saying-goodbye-to-search-cpan-org/ for details.'
FROM packages
WHERE
	homepage SIMILAR TO 'https?://search.cpan.org(/%%)?';

-- update counts for repositories
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
	url
)
SELECT
	unnest(downloads)
FROM packages
UNION
SELECT
	homepage
FROM packages
WHERE
	homepage IS NOT NULL AND
	repo NOT IN('cpan', 'pypi', 'rubygems', 'cran')
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
	num_maintainers = (SELECT count(*) FROM maintainers WHERE num_packages > 0);

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
		num_metapackages_problematic,
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

--------------------------------------------------------------------------------
-- Hack: avoid sequence overflows (especially for repositories table)
--------------------------------------------------------------------------------
-- XXX: this one is not really helpful currently as packages are INSERTed, not UPSERTed
-- if packages id overflow becomes problem, we may enable CYCLE on packages id sequence
--SELECT setval(pg_get_serial_sequence('packages', 'id'), (select max(id) + 1 FROM packages));
SELECT setval(pg_get_serial_sequence('metapackages', 'id'), (select max(id) + 1 FROM metapackages));
SELECT setval(pg_get_serial_sequence('repositories', 'id'), (select max(id) + 1 FROM repositories));
SELECT setval(pg_get_serial_sequence('maintainers', 'id'), (select max(id) + 1 FROM maintainers));
