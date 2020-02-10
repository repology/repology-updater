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
	packages.visiblename,
	packages.effname,
	unnest(CASE WHEN packages.maintainers = '{}' THEN '{null}' ELSE packages.maintainers END),
	'Homepage link "' ||
		links.url ||
		'" is dead (' ||
		CASE
			WHEN links.ipv4_status_code=-1 THEN 'unknown error'
			WHEN links.ipv4_status_code=-100 THEN 'connect timeout'
			WHEN links.ipv4_status_code=-101 THEN 'invalid url'
			WHEN links.ipv4_status_code=-102 THEN 'host blacklisted for being taken over'
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
	packages.visiblename,
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
	visiblename,
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
	visiblename,
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
	visiblename,
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
	visiblename,
	effname,
	unnest(CASE WHEN packages.maintainers = '{}' THEN '{null}' ELSE packages.maintainers END),
	'Homepage link "' || homepage || '" points to CPAN which was discontinued. The link should be updated to https://metacpan.org (probably along with download URLs). See https://www.perl.com/article/saying-goodbye-to-search-cpan-org/ for details.'
FROM packages
WHERE
	homepage SIMILAR TO 'https?://search.cpan.org(/%%)?';
