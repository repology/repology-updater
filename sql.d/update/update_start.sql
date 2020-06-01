-- Copyright (C) 2016-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

CREATE TEMPORARY TABLE changed_projects (
	effname text NOT NULL
)
ON COMMIT DROP;

CREATE TEMPORARY TABLE incoming_packages (
	-- parsed, immutable
    repo text NOT NULL,
    family text NOT NULL,
    subrepo text,

    name text NULL,
    srcname text NULL,
    binname text NULL,
    trackname text NOT NULL,
    visiblename text NOT NULL,
    projectname_seed text NOT NULL,

    origversion text NOT NULL,
    rawversion text NOT NULL,

    arch text,

    maintainers text[],
    category text,
    comment text,
    homepage text,
    licenses text[],
    downloads text[],

    extrafields jsonb NOT NULL,

	cpe_vendor text NULL,
	cpe_product text NULL,
	cpe_edition text NULL,
	cpe_lang text NULL,
	cpe_sw_edition text NULL,
	cpe_target_sw text NULL,
	cpe_target_hw text NULL,
	cpe_other text NULL,

    -- calculated
    effname text NOT NULL,
    version text NOT NULL,
    versionclass smallint,

    flags integer NOT NULL,
    shadow bool NOT NULL,

    flavors text[],
    branch text NULL
)
ON COMMIT DROP;
