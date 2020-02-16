-- Copyright (C) 2020 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

-- pass 1, basic counters
WITH old AS (
	SELECT
		unnest(maintainers) AS maintainer_name,

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

		count(DISTINCT effname) AS num_projects,
		count(DISTINCT effname) FILTER(WHERE versionclass = 1 OR versionclass = 4 OR versionclass = 5) AS num_projects_newest,
		count(DISTINCT effname) FILTER(WHERE versionclass = 2) AS num_projects_outdated,
		count(DISTINCT effname) FILTER(WHERE versionclass = 3 OR versionclass = 7 OR versionclass = 8) AS num_projects_problematic
	FROM old_packages
	GROUP BY maintainer_name
), new AS (
	SELECT
		unnest(maintainers) AS maintainer_name,

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

		count(DISTINCT effname) AS num_projects,
		count(DISTINCT effname) FILTER(WHERE versionclass = 1 OR versionclass = 4 OR versionclass = 5) AS num_projects_newest,
		count(DISTINCT effname) FILTER(WHERE versionclass = 2) AS num_projects_outdated,
		count(DISTINCT effname) FILTER(WHERE versionclass = 3 OR versionclass = 7 OR versionclass = 8) AS num_projects_problematic
	FROM incoming_packages
	GROUP BY maintainer_name
)
UPDATE maintainers
SET
	num_packages = maintainers.num_packages + coalesce(new.num_packages, 0) - coalesce(old.num_packages, 0),
	num_packages_newest = maintainers.num_packages_newest + coalesce(new.num_packages_newest, 0) - coalesce(old.num_packages_newest, 0),
	num_packages_outdated = maintainers.num_packages_outdated + coalesce(new.num_packages_outdated, 0) - coalesce(old.num_packages_outdated, 0),
	num_packages_ignored = maintainers.num_packages_ignored + coalesce(new.num_packages_ignored, 0) - coalesce(old.num_packages_ignored, 0),
	num_packages_unique = maintainers.num_packages_unique + coalesce(new.num_packages_unique, 0) - coalesce(old.num_packages_unique, 0),
	num_packages_devel = maintainers.num_packages_devel + coalesce(new.num_packages_devel, 0) - coalesce(old.num_packages_devel, 0),
	num_packages_legacy = maintainers.num_packages_legacy + coalesce(new.num_packages_legacy, 0) - coalesce(old.num_packages_legacy, 0),
	num_packages_incorrect = maintainers.num_packages_incorrect + coalesce(new.num_packages_incorrect, 0) - coalesce(old.num_packages_incorrect, 0),
	num_packages_untrusted = maintainers.num_packages_untrusted + coalesce(new.num_packages_untrusted, 0) - coalesce(old.num_packages_untrusted, 0),
	num_packages_noscheme = maintainers.num_packages_noscheme + coalesce(new.num_packages_noscheme, 0) - coalesce(old.num_packages_noscheme, 0),
	num_packages_rolling = maintainers.num_packages_rolling + coalesce(new.num_packages_rolling, 0) - coalesce(old.num_packages_rolling, 0),

	num_projects = maintainers.num_projects + coalesce(new.num_projects, 0) - coalesce(old.num_projects, 0),
	num_projects_newest = maintainers.num_projects_newest + coalesce(new.num_projects_newest, 0) - coalesce(old.num_projects_newest, 0),
	num_projects_outdated = maintainers.num_projects_outdated + coalesce(new.num_projects_outdated, 0) - coalesce(old.num_projects_outdated, 0),
	num_projects_problematic = maintainers.num_projects_problematic + coalesce(new.num_projects_problematic, 0) - coalesce(old.num_projects_problematic, 0),

	orphaned_at = CASE WHEN maintainers.num_packages + coalesce(new.num_packages, 0) - coalesce(old.num_packages, 0) = 0 THEN now() ELSE NULL END
FROM old FULL OUTER JOIN new USING(maintainer_name)
WHERE maintainers.maintainer = maintainer_name;

-- pass 3, per-category counters
WITH old AS (
	SELECT
		unnest(maintainers) AS maintainer_name,
		category,
		count(DISTINCT effname) AS num_projects
	FROM old_packages
	WHERE category IS NOT NULL
	GROUP BY maintainer_name, category
), new AS (
	SELECT
		unnest(maintainers) AS maintainer_name,
		category,
		count(DISTINCT effname) AS num_projects
	FROM incoming_packages
	WHERE category IS NOT NULL
	GROUP BY maintainer_name, category
), delta AS (
	SELECT
		maintainer_name,
		category,
		coalesce(new.num_projects, 0) - coalesce(old.num_projects, 0) AS num_projects
	FROM old FULL OUTER JOIN new USING(maintainer_name, category)
	WHERE coalesce(new.num_projects, 0) - coalesce(old.num_projects, 0) != 0
), old_state AS (
	SELECT
		maintainer AS maintainer_name,
		(jsonb_each_text(num_projects_per_category)).key AS category,
		(jsonb_each_text(num_projects_per_category)).value::integer as num_projects
	FROM maintainers
	WHERE maintainer IN (SELECT maintainer_name FROM delta)
), new_state AS (
	SELECT
		maintainer_name,
		category,
		coalesce(old_state.num_projects, 0) + coalesce(delta.num_projects, 0) AS num_projects
	FROM old_state FULL OUTER JOIN delta USING(maintainer_name, category)
	WHERE
		coalesce(old_state.num_projects, 0) + coalesce(delta.num_projects, 0) != 0
)
UPDATE maintainers
SET
	num_projects_per_category = tmp.num_projects_per_category
FROM (
	SELECT
		maintainer_name,
		json_object_agg(category, num_projects) AS num_projects_per_category
	FROM new_state
	GROUP BY maintainer_name
) AS tmp
WHERE maintainers.maintainer = tmp.maintainer_name;

{% if analyze %}
ANALYZE maintainers;
{% endif %}
