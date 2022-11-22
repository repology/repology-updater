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

-- Given an url, computes a digest for it which can be used to compare similar URLs
-- Rougly, "http://FOO.COM/bar/" and "https://www.foo.com/bar#baz"
-- both become "foo.com/bar", so the packages using these urls would
-- be detected as related
CREATE OR REPLACE FUNCTION simplify_url(url text) RETURNS text AS $$
BEGIN
	RETURN regexp_replace(
		regexp_replace(
			regexp_replace(
				regexp_replace(
					regexp_replace(
						regexp_replace(
							-- lowercase
							lower(url),
							-- unwrap archive.org links
							'^https?://web.archive.org/web/([0-9]{10}[^/]*/|\*/)?', ''
						),
						-- drop fragment
						'#.*$', ''
					),
					-- drop parameters
					'\?.*$', ''
				),
				-- drop trailing slash
				'/$', ''
			),
			-- drop schema
			'^https?://', ''
		),
		-- drop www.
		'^www\.', ''
	);
END;
$$ LANGUAGE plpgsql IMMUTABLE PARALLEL SAFE RETURNS NULL ON NULL INPUT;

-- Checks whether version set has effectively changed
CREATE OR REPLACE FUNCTION version_set_changed(old text[], new text[]) RETURNS bool AS $$
BEGIN
	RETURN
		(
			old IS NOT NULL AND
			new IS NOT NULL AND
			version_compare2(old[1], new[1]) != 0
		) OR (old IS NULL) != (new IS NULL);
END;
$$ LANGUAGE plpgsql IMMUTABLE PARALLEL SAFE CALLED ON NULL INPUT;

-- Returns repositories which may be logged as added/removed for projects feed
-- Ignores incomplete and inactive repos
CREATE OR REPLACE FUNCTION get_added_repos_for_projects_feed(oldrepos text[], newrepos text[]) RETURNS text[] AS $$
BEGIN
	RETURN
		array(
			(
				SELECT unnest(newrepos)
				EXCEPT
				SELECT unnest(oldrepos)
			)
			INTERSECT
			SELECT name FROM repositories WHERE state = 'active' AND NOT incomplete
		);
END;
$$ LANGUAGE plpgsql STABLE RETURNS NULL ON NULL INPUT;

-- Checks statuses and flags mask and returns whether it should be treated as ignored
CREATE OR REPLACE FUNCTION is_ignored_by_masks(statuses_mask integer, flags_mask integer) RETURNS boolean AS $$
BEGIN
	RETURN (statuses_mask & ((1<<3) | (1<<7) | (1<<8) | (1<<9) | (1<<10)))::boolean OR (flags_mask & ((1<<2) | (1<<3) | (1<<4) | (1<<5) | (1<<7)))::boolean;
END;
$$ LANGUAGE plpgsql IMMUTABLE PARALLEL SAFE RETURNS NULL ON NULL INPUT;

-- Similar to nullif, but with less comparison
CREATE OR REPLACE FUNCTION nullifless(value1 double precision, value2 double precision) RETURNS double precision AS $$
BEGIN
	RETURN CASE WHEN value1 < value2 THEN NULL ELSE value1 END;
END;
$$ LANGUAGE plpgsql IMMUTABLE PARALLEL SAFE RETURNS NULL ON NULL INPUT;

-- Used for related packages discovery
CREATE OR REPLACE FUNCTION project_get_related(source_project_id integer, maxresults integer)
	RETURNS TABLE(
		related_project_id integer,
		rank float
	)
AS $$
DECLARE
	continue boolean := true;
BEGIN
	-- Seed the algorithm with base project
	CREATE TEMPORARY TABLE related ON COMMIT DROP AS
	SELECT
		source_project_id AS metapackage_id,
		1.0::float AS rank;

	-- Recursively discover new projects through project homepage links,
	-- calculating rank along the way.
	-- The rank calculation algorithm is roughly as follows:
	WHILE continue LOOP
		CREATE TEMPORARY TABLE new_related ON COMMIT DROP AS
		-- Step 1 - follow links for known projects
		WITH pass1_1 AS (
			SELECT
				urlhash,
				-- 1.1. For each project taking part in this iteration, take it's rank and
				-- divide it among its links, taking link weight into account.
				related.rank / (SELECT count(*) FROM related) / count(*) OVER (PARTITION BY metapackage_id) * weight AS rank
			FROM related INNER JOIN url_relations USING(metapackage_id)
		), pass1_2 AS (
			SELECT
				urlhash,
				-- 1.2. Weight from multiple projects on a single link is summed.
				sum(pass1_1.rank) AS rank,
				count(*) AS incoming_projects
			FROM pass1_1
			GROUP BY urlhash

		-- Step 2 - projects from links discovered on step 1
		), pass2_1 AS (
			SELECT
				metapackage_id,
				-- 2.1. Now, for each link, divide its rank among the projects it points
				-- to, ignoring projects the rank came from on this iteration.
				-- Link weights are not accounted for second time.
				pass1_2.rank / (nullif(count(*) OVER (PARTITION BY urlhash), incoming_projects) - incoming_projects) AS rank
			FROM pass1_2 INNER JOIN url_relations USING(urlhash)
		), pass2_2 AS (
			SELECT
				metapackage_id,
				-- 2.2. Similar to 1.2, rank passed by all links to a single project is summed
				sum(pass2_1.rank) AS rank
			FROM pass2_1
			GROUP BY metapackage_id
		)
		-- 3. Merge with result of previous iteration
		SELECT
			metapackage_id,
			greatest(related.rank, pass2_2.rank) AS rank
		FROM related FULL OUTER JOIN pass2_2 USING(metapackage_id)
		ORDER BY rank DESC, metapackage_id
		LIMIT maxresults;

		-- If we couldn't find any more relevant projects on this step, stop
		SELECT INTO continue (SELECT sum(new_related.rank) FROM new_related) > (SELECT sum(related.rank) FROM related);

		DROP TABLE related;
		ALTER TABLE new_related RENAME TO related;
	END LOOP;

	RETURN QUERY
	SELECT
		metapackage_id,
		-- Since it's common for the ranks calculated above to be very small (like 1e-8),
		-- perform logarithmic conversion to make them more human-readable. It mapping is
		-- as follows: 1.0 → 100, 0.1 → 90, 0.01 → 80, 0.001 → 70 etc., but never less
		-- than zero
		greatest(0.0, 100.0 + log(related.rank) * 10.0)
	FROM
		related;
END; $$ LANGUAGE plpgsql VOLATILE RETURNS NULL ON NULL INPUT;

-- Translates string urls to link ids within links package field
CREATE OR REPLACE FUNCTION translate_links(links json) RETURNS json AS $$
BEGIN
	RETURN
		(
			WITH expanded AS (
				SELECT
					json_array_elements(links)->0 AS link_type,
					json_array_elements(links)->>1 AS url,
					json_array_elements(links)->>2 AS fragment
			), translated AS (
				SELECT
					link_type,
					(SELECT id FROM links WHERE links.url = expanded.url) AS link_id,
					fragment
				FROM expanded
			), joined AS (
				SELECT
					CASE
						WHEN fragment IS NULL
						THEN json_build_array(link_type, link_id)
						ELSE json_build_array(link_type, link_id, fragment)
					END AS link
				FROM translated
			)
			SELECT json_agg(link) FROM joined
		);
END;
$$ LANGUAGE plpgsql STABLE RETURNS NULL ON NULL INPUT;
