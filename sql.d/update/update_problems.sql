-- Copyright (C) 2016-2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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
-- @param analyze=True
--------------------------------------------------------------------------------

DELETE FROM problems
WHERE effname IN (SELECT effname FROM changed_projects);

-- add different kinds of problems
WITH packages_links_expanded AS (
	SELECT DISTINCT
		id,
		repo,
		visiblename,
		effname,
		maintainers,
		(json_array_elements(links)->>0)::integer AS link_type,
		(json_array_elements(links)->>1)::integer AS link_id
	FROM changed_projects INNER JOIN packages USING(effname)
), packages_links_maintainers_expanded AS (
	SELECT
		id,
		repo,
		visiblename,
		effname,
		unnest(coalesce(maintainers, '{null}'::text[])) AS maintainer,
		link_type,
		link_id
	FROM packages_links_expanded
), packages_homepages AS (
	SELECT DISTINCT
		packages_links_maintainers_expanded.id,
		repo,
		visiblename,
		effname,
		maintainer,
		url,
		CASE
			WHEN coalesce(ipv4_status_code, 0) = 200 OR coalesce(ipv6_status_code, 0) = 200 THEN 200
			WHEN coalesce(ipv4_status_code, 0) BETWEEN -99 AND 0 THEN coalesce(ipv6_status_code, 0)
			ELSE coalesce(ipv4_status_code, 0)
		END AS status_code,
		failure_streak,
		last_success,
		first_extracted,
		coalesce(ipv4_permanent_redirect_target, ipv6_permanent_redirect_target) AS permanent_redirect_target,
		link_type
	FROM packages_links_maintainers_expanded INNER JOIN links ON(links.id = link_id)
	WHERE link_type IN (0, 1, 28)  -- UPSTREAM_HOMEPAGE, UPSTREAM_DOWNLOAD, UPSTREAM_DOWNLOAD_PAGE
), homepage_problems AS (
	SELECT id, repo, visiblename, effname, maintainer,
		'homepage_dead'::problem_type AS problem_type,
		jsonb_build_object('url', url, 'code', status_code) AS data
	FROM packages_homepages
	WHERE
		link_type = 0 AND
		status_code NOT BETWEEN -99 AND 0 AND
		status_code != 200 AND
		failure_streak >= 3 AND
		(
			(last_success IS NULL AND first_extracted < now() - INTERVAL '30' DAY) OR
			last_success < now() - INTERVAL '30' DAY
		)

	UNION ALL SELECT id, repo, visiblename, effname, maintainer,
		'homepage_permanent_https_redirect'::problem_type AS problem_type,
		jsonb_build_object('url', url, 'target', permanent_redirect_target) AS data
	FROM packages_homepages
	WHERE
		link_type = 0 AND
		replace(url, 'http://', 'https://') = permanent_redirect_target

	UNION ALL SELECT id, repo, visiblename, effname, maintainer,
		'homepage_discontinued_google'::problem_type AS problem_type,
		jsonb_build_object('url', url) AS data
	FROM packages_homepages
	WHERE
		link_type = 0 AND
		url SIMILAR TO 'https?://([^/]+.)?googlecode.com(/%%)?' OR
		url SIMILAR TO 'https?://code.google.com(/%%)?'

	UNION ALL SELECT id, repo, visiblename, effname, maintainer,
		'homepage_discontinued_codeplex'::problem_type AS problem_type,
		jsonb_build_object('url', url) AS data
	FROM packages_homepages
	WHERE
		link_type = 0 AND
		url SIMILAR TO 'https?://([^/]+.)?codeplex.com(/%%)?'

	UNION ALL SELECT id, repo, visiblename, effname, maintainer,
		'homepage_discontinued_gna'::problem_type AS problem_type,
		jsonb_build_object('url', url) AS data
	FROM packages_homepages
	WHERE
		link_type = 0 AND
		url SIMILAR TO 'https?://([^/]+.)?gna.org(/%%)?'

	UNION ALL SELECT id, repo, visiblename, effname, maintainer,
		'homepage_sourceforge_missing_trailing_slash'::problem_type AS problem_type,
		jsonb_build_object('url', url) AS data
	FROM packages_homepages
	WHERE
		link_type = 0 AND
		url SIMILAR TO 'https?://sourceforge.net/projects/[^/]+'

	UNION ALL SELECT id, repo, visiblename, effname, maintainer,
		'homepage_discontinued_cpan'::problem_type AS problem_type,
		jsonb_build_object('url', url) AS data
	FROM packages_homepages
	WHERE
		link_type = 0 AND
		url SIMILAR TO 'https?://search.cpan.org(/%%)?'

	UNION ALL SELECT id, repo, visiblename, effname, maintainer,
		'download_dead'::problem_type AS problem_type,
		jsonb_build_object('url', url, 'code', status_code) AS data
	FROM packages_homepages
	WHERE
		link_type = 1 AND
		status_code NOT BETWEEN -99 AND 0 AND
		status_code != 200 AND
		failure_streak >= 3 AND
		(
			(last_success IS NULL AND first_extracted < now() - INTERVAL '30' DAY) OR
			last_success < now() - INTERVAL '30' DAY
		)

	UNION ALL SELECT id, repo, visiblename, effname, maintainer,
		'download_permanent_https_redirect'::problem_type AS problem_type,
		jsonb_build_object('url', url, 'target', permanent_redirect_target) AS data
	FROM packages_homepages
	WHERE
		link_type = 1 AND
		replace(url, 'http://', 'https://') = permanent_redirect_target
)
INSERT INTO problems(package_id, repo, name, effname, maintainer, "type", data)
SELECT id, repo, visiblename, effname, maintainer, problem_type, data
FROM homepage_problems;

INSERT INTO problems(package_id, repo, name, effname, maintainer, "type", data)
SELECT DISTINCT
	id,
	repo,
	visiblename,
	effname,
	unnest(coalesce(packages.maintainers, '{null}'::text[])),
	'cpe_unreferenced'::problem_type,
	jsonb_build_object(
		'cpe',
		jsonb_build_object(
			'cpe_vendor', coalesce(cpe_vendor, '*'),
			'cpe_product', coalesce(cpe_product, '*'),
			'cpe_edition', coalesce(cpe_edition, '*'),
			'cpe_lang', coalesce(cpe_lang, '*'),
			'cpe_sw_edition', coalesce(cpe_sw_edition, '*'),
			'cpe_target_sw', coalesce(cpe_target_sw, '*'),
			'cpe_target_hw', coalesce(cpe_target_hw, '*'),
			'cpe_other', coalesce(cpe_other, '*')
		),
		'suggestions',
		(
			SELECT jsonb_agg(DISTINCT
				jsonb_build_object(
					'cpe_vendor', cpe_vendor,
					'cpe_product', cpe_product,
					'cpe_edition', cpe_edition,
					'cpe_lang', cpe_lang,
					'cpe_sw_edition', cpe_sw_edition,
					'cpe_target_sw', cpe_target_sw,
					'cpe_target_hw', cpe_target_hw,
					'cpe_other', cpe_other
				)
			)
			FROM vulnerable_projects
			WHERE effname = packages.effname
		)
	)
FROM changed_projects
INNER JOIN packages USING(effname)
WHERE
	cpe_product IS NOT NULL
	AND NOT EXISTS (
		SELECT *
		FROM vulnerable_cpes
		WHERE
			cpe_product = packages.cpe_product AND
			coalesce(nullif(cpe_vendor, '*') = nullif(packages.cpe_vendor, '*'), TRUE) AND
			coalesce(nullif(cpe_edition, '*') = nullif(packages.cpe_edition, '*'), TRUE) AND
			coalesce(nullif(cpe_lang, '*') = nullif(packages.cpe_lang, '*'), TRUE) AND
			coalesce(nullif(cpe_sw_edition, '*') = nullif(packages.cpe_sw_edition, '*'), TRUE) AND
			coalesce(nullif(cpe_target_sw, '*') = nullif(packages.cpe_target_sw, '*'), TRUE) AND
			coalesce(nullif(cpe_target_hw, '*') = nullif(packages.cpe_target_hw, '*'), TRUE) AND
			coalesce(nullif(cpe_other, '*') = nullif(packages.cpe_other, '*'), TRUE)
	)
	AND NOT EXISTS (
		SELECT *
		FROM cpe_dictionary
		WHERE
			cpe_product = packages.cpe_product AND
			coalesce(nullif(cpe_vendor, '*') = nullif(packages.cpe_vendor, '*'), TRUE) AND
			coalesce(nullif(cpe_edition, '*') = nullif(packages.cpe_edition, '*'), TRUE) AND
			coalesce(nullif(cpe_lang, '*') = nullif(packages.cpe_lang, '*'), TRUE) AND
			coalesce(nullif(cpe_sw_edition, '*') = nullif(packages.cpe_sw_edition, '*'), TRUE) AND
			coalesce(nullif(cpe_target_sw, '*') = nullif(packages.cpe_target_sw, '*'), TRUE) AND
			coalesce(nullif(cpe_target_hw, '*') = nullif(packages.cpe_target_hw, '*'), TRUE) AND
			coalesce(nullif(cpe_other, '*') = nullif(packages.cpe_other, '*'), TRUE)
	);

INSERT INTO problems(package_id, repo, name, effname, maintainer, "type", data)
SELECT DISTINCT
	id,
	repo,
	visiblename,
	effname,
	unnest(coalesce(packages.maintainers, '{null}'::text[])),
	'cpe_missing'::problem_type,
	jsonb_build_object('suggestions',
		(
			SELECT jsonb_agg(DISTINCT
				jsonb_build_object(
					'cpe_vendor', cpe_vendor,
					'cpe_product', cpe_product,
					'cpe_edition', cpe_edition,
					'cpe_lang', cpe_lang,
					'cpe_sw_edition', cpe_sw_edition,
					'cpe_target_sw', cpe_target_sw,
					'cpe_target_hw', cpe_target_hw,
					'cpe_other', cpe_other
				)
			)
			FROM vulnerable_projects
			WHERE effname = packages.effname
		)
	)
FROM changed_projects
INNER JOIN packages USING(effname)
WHERE
	(
		SELECT used_package_fields @> ARRAY['cpe_product'] FROM repositories WHERE name = packages.repo
	)
	AND cpe_product IS NULL
	AND EXISTS (SELECT * FROM vulnerable_projects WHERE effname = packages.effname);

{% if analyze %}
ANALYZE problems;
{% endif %}
