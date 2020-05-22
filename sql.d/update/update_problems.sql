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
	jsonb_build_object('vendor', cpe_vendor, 'product', cpe_product, 'suggestions',
		(
			SELECT jsonb_agg(DISTINCT jsonb_build_object('vendor', cpe_vendor, 'product', cpe_product))
			FROM all_cpes
			INNER JOIN vulnerable_versions USING (cpe_vendor, cpe_product)
			WHERE all_cpes.effname = packages.effname
		)
	)
FROM changed_projects
INNER JOIN packages USING(effname)
WHERE
    cpe_vendor IS NOT NULL AND
    cpe_product IS NOT NULL AND
    NOT EXISTS (
        SELECT *
        FROM vulnerable_versions
        WHERE
            vulnerable_versions.cpe_vendor = packages.cpe_vendor AND
            vulnerable_versions.cpe_product = packages.cpe_product
    ) AND
    NOT EXISTS (
        SELECT *
        FROM cpe_dictionary
        WHERE
            cpe_dictionary.cpe_vendor = packages.cpe_vendor AND
            cpe_dictionary.cpe_product = packages.cpe_product
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
			SELECT jsonb_agg(DISTINCT jsonb_build_object('vendor', cpe_vendor, 'product', cpe_product))
			FROM all_cpes
			INNER JOIN vulnerable_versions USING (cpe_vendor, cpe_product)
			WHERE all_cpes.effname = packages.effname
		)
	)
FROM changed_projects
INNER JOIN packages USING(effname)
WHERE
	(
		SELECT used_package_fields @> ARRAY['cpe_vendor'] FROM repositories WHERE repositories.name = packages.repo
	) AND
    cpe_vendor IS NULL AND
    EXISTS (
        SELECT *
        FROM all_cpes
		INNER JOIN vulnerable_versions USING (cpe_vendor, cpe_product)
		WHERE all_cpes.effname = packages.effname
    );

{% if analyze %}
ANALYZE problems;
{% endif %}
