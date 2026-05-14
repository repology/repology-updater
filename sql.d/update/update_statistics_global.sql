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

UPDATE statistics SET
	num_metapackages = (SELECT count(*) FROM metapackages WHERE num_repos_nonshadow > 0),
	num_problems = (SELECT count(*) FROM problems),
	num_maintainers = (SELECT count(*) FROM maintainers WHERE num_packages > 0),
	num_reports_total = (SELECT count(*) FROM reports),
	num_reports_open = (SELECT count(*) FROM reports WHERE accepted IS NULL),
	num_links_total = (SELECT count(*) FROM links WHERE refcount > 0),
	num_links_overdue = (SELECT count(*) FROM links WHERE refcount > 0 AND next_check < now()),
	num_links_checkable = (SELECT count(*) FROM links WHERE refcount > 0 AND (coalesce(ipv4_status_code, 0) NOT BETWEEN -6 AND 0 OR coalesce(ipv6_status_code, 0) NOT BETWEEN -6 AND 0)),
	num_links_alive = (SELECT count(*) FROM links WHERE refcount > 0 AND (ipv4_status_code = 200 OR ipv6_status_code = 200)),
	num_links_alive_ipv6 = (SELECT count(*) FROM links WHERE refcount > 0 AND ipv6_status_code = 200),
	num_links_extracted_checkable = (SELECT count(*) FROM links WHERE refcount > 0 AND priority AND (coalesce(ipv4_status_code, 0) NOT BETWEEN -6 AND 0 OR coalesce(ipv6_status_code, 0) NOT BETWEEN -6 AND 0)),
	num_links_extracted_alive = (SELECT count(*) FROM links WHERE refcount > 0 AND priority AND (ipv4_status_code = 200 OR ipv6_status_code = 200)),
	num_links_extracted_alive_ipv6 = (SELECT count(*) FROM links WHERE refcount > 0 AND priority AND ipv6_status_code = 200);
