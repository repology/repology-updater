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

-- !!add_report(effname, need_verignore, need_split, need_merge, comment)
INSERT INTO reports (
	created,
	effname,
	need_verignore,
	need_split,
	need_merge,
	comment
) VALUES (
	now(),
	%s,
	%s,
	%s,
	%s,
	%s
);

-- !!get_reports_count(effname) -> single value
SELECT
	count(*)
FROM reports
WHERE effname = %s;

-- !!get_reports(effname) -> array of dicts
SELECT
	id,
	now() - created AS created_ago,
	effname,
	need_verignore,
	need_split,
	need_merge,
	comment,
	reply,
	accepted
FROM reports
WHERE effname = %s
ORDER BY created DESC;
