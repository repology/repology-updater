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
-- @param analyze=True
--------------------------------------------------------------------------------

DELETE FROM problems
WHERE effname IN (SELECT effname FROM changed_projects);

-- add different kinds of problems
INSERT INTO problems(package_id, repo, name, effname, maintainer, "type", data)
SELECT DISTINCT
	packages.id,
	packages.repo,
	packages.visiblename,
	packages.effname,
	unnest(CASE WHEN packages.maintainers = '{}' THEN '{null}' ELSE packages.maintainers END),
	'homepage_dead'::problem_type,
	jsonb_build_object('url', links.url, 'code', links.ipv4_status_code)
FROM changed_projects
INNER JOIN packages USING(effname)
INNER JOIN links ON (packages.homepage = links.url)
WHERE
	NOT links.ipv4_success AND
	(
		(links.ipv4_last_success IS NULL AND links.first_extracted < now() - INTERVAL '30' DAY) OR
		links.ipv4_last_success < now() - INTERVAL '30' DAY
	);

INSERT INTO problems(package_id, repo, name, effname, maintainer, "type", data)
SELECT DISTINCT
	packages.id,
	packages.repo,
	packages.visiblename,
	packages.effname,
	unnest(CASE WHEN packages.maintainers = '{}' THEN '{null}' ELSE packages.maintainers END),
	'homepage_permanent_https_redirect'::problem_type,
	jsonb_build_object('url', links.url, 'target', links.ipv4_permanent_redirect_target)
FROM changed_projects
INNER JOIN packages USING(effname)
INNER JOIN links ON (packages.homepage = links.url)
WHERE
	replace(links.url, 'http://', 'https://') = links.ipv4_permanent_redirect_target;

INSERT INTO problems(package_id, repo, name, effname, maintainer, "type", data)
SELECT DISTINCT
	id,
	repo,
	visiblename,
	effname,
	unnest(CASE WHEN packages.maintainers = '{}' THEN '{null}' ELSE packages.maintainers END),
	'homepage_discontinued_google'::problem_type,
	jsonb_build_object('url', homepage)
FROM changed_projects
INNER JOIN packages USING(effname)
WHERE
	homepage SIMILAR TO 'https?://([^/]+.)?googlecode.com(/%%)?' OR
	homepage SIMILAR TO 'https?://code.google.com(/%%)?';

INSERT INTO problems(package_id, repo, name, effname, maintainer, "type", data)
SELECT DISTINCT
	id,
	repo,
	visiblename,
	effname,
	unnest(CASE WHEN packages.maintainers = '{}' THEN '{null}' ELSE packages.maintainers END),
	'homepage_discontinued_codeplex'::problem_type,
	jsonb_build_object('url', homepage)
FROM changed_projects
INNER JOIN packages USING(effname)
WHERE
	homepage SIMILAR TO 'https?://([^/]+.)?codeplex.com(/%%)?';

INSERT INTO problems(package_id, repo, name, effname, maintainer, "type", data)
SELECT DISTINCT
	id,
	repo,
	visiblename,
	effname,
	unnest(CASE WHEN packages.maintainers = '{}' THEN '{null}' ELSE packages.maintainers END),
	'homepage_discontinued_gna'::problem_type,
	jsonb_build_object('url', homepage)
FROM changed_projects
INNER JOIN packages USING(effname)
WHERE
	homepage SIMILAR TO 'https?://([^/]+.)?gna.org(/%%)?';

INSERT INTO problems(package_id, repo, name, effname, maintainer, "type", data)
SELECT DISTINCT
	id,
	repo,
	visiblename,
	effname,
	unnest(CASE WHEN packages.maintainers = '{}' THEN '{null}' ELSE packages.maintainers END),
	'homepage_discontinued_cpan'::problem_type,
	jsonb_build_object('url', homepage)
FROM changed_projects
INNER JOIN packages USING(effname)
WHERE
	homepage SIMILAR TO 'https?://search.cpan.org(/%%)?';

INSERT INTO problems(package_id, repo, name, effname, maintainer, "type", data)
SELECT DISTINCT
	id,
	repo,
	visiblename,
	effname,
	unnest(CASE WHEN packages.maintainers = '{}' THEN '{null}' ELSE packages.maintainers END),
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
	unnest(CASE WHEN packages.maintainers = '{}' THEN '{null}' ELSE packages.maintainers END),
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
