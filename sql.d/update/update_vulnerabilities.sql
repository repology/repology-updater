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

UPDATE incoming_packages
SET
	flags = flags | (1 << 16)
WHERE
	versionclass != 10 -- ROLLING
	AND EXISTS (
		-- XXX: this lookup could be faster if vulnerable_versions had version fields
		-- included into index
		SELECT *
		FROM vulnerable_versions INNER JOIN all_cpes USING (cpe_vendor, cpe_product)
		WHERE
			all_cpes.effname = incoming_packages.effname AND
			coalesce(
				version_compare2(incoming_packages.version, vulnerable_versions.start_version) >
				CASE WHEN vulnerable_versions.start_version_excluded THEN 0 ELSE -1 END,
				true
			) AND
			version_compare2(incoming_packages.version, vulnerable_versions.end_version) <
			CASE WHEN vulnerable_versions.end_version_excluded THEN 0 ELSE 1 END
	)
;
