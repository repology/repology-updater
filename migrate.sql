alter table packages add column pkgconfig_names text[] NULL;

CREATE TYPE project_identifier_type AS enum(
	'pkgconfig'
);

CREATE TABLE project_identifiers (
	project_id integer NOT NULL,
	"type" project_identifier_type NOT NULL,
	identifier text NOT NULL
);

CREATE INDEX ON project_identifiers(project_id);
CREATE INDEX ON project_identifiers(identifier);
