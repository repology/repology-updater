# Running repology

## Dependencies

### For running

Needed for the core:

- [Python](https://www.python.org/) 3.7+
- Python module [pyyaml](http://pyyaml.org/)
- Python module [Jinja2](http://jinja.pocoo.org/)
- Python module [libversion](https://pypi.python.org/pypi/libversion) (also requires [libversion](https://github.com/repology/libversion) C library)
- Python module [psycopg](http://initd.org/psycopg/)

- [PostgreSQL](https://www.postgresql.org/) 10.0+
- PostgreSQL extension [libversion](https://github.com/repology/postgresql-libversion)

Needed for fetching/parsing repository data:

- Python module [requests](http://python-requests.org/)
- Python module [rubymarshal](https://github.com/d9pouces/RubyMarshal)
- Python module [lxml](http://lxml.de/)
- Python module [rpm](http://rpm.org/) (comes with RPM package manager)
- Python module [jsonslicer](https://pypi.org/project/jsonslicer/)
- Python module [pyparsing](https://github.com/pyparsing/pyparsing/)
- Python module sqlite3
- [git](https://git-scm.com/)
- [rsync](https://rsync.samba.org/)
- [tclsh](https://www.tcl.tk/) and [tcllib](https://www.tcl.tk/)

Needed for web-application:

- Python module [flask](http://flask.pocoo.org/)
- Python module [pillow](https://pypi.python.org/pypi/Pillow)
- Python module [pytz](https://pypi.python.org/pypi/pytz)

### For development

Optional, for doing HTML validation when running tests:
- Python module [pytidylib](https://pypi.python.org/pypi/pytidylib) and [tidy-html5](http://www.html-tidy.org/) library

Optional, for checking schemas of configuration files:
- Python module [voluptuous](https://pypi.python.org/pypi/voluptuous)

Optional, for python code linting:
- Python module [flake8](https://pypi.python.org/pypi/flake8)
- Python module [flake8-builtins](https://pypi.python.org/pypi/flake8-builtins)
- Python module [flake8-import-order](https://pypi.python.org/pypi/flake8-import-order)
- Python module [flake8-quotes](https://pypi.python.org/pypi/flake8-quotes)
- Python module [mypy](http://mypy-lang.org/)

## Usage

### Preparing

Since repology rules live in separate repository you'll need to
clone it first. The location may be arbitrary, but `rules.d`
subdirectory is what default configuration file points to, so
using it is the most simple way.

```
git clone https://github.com/repology/repology-rules.git rules.d
```

### Configuration

First, you may need to tune settings which are shared by all repology
utilities, such as directory for storing downloaded repository state
or DSN (string which specifies how to connect to PostgreSQL database).
See `repology.conf.default` for default values, create `repology.conf`
in the same directory to override them (don't edit `repology.conf.default`!)
or specify path to alternative config via `REPOLOGY_SETTINGS`
environment variable, or override settings via command line.

By default, repology uses `./_state` directory for storing raw and parsed
repository data and `repology/repology/repology` database/user/password
on localhost.

### Creating the database

For the following steps you'll need to set up the database. Ensure
PostgreSQL server is up and running, and execute the following
commands to create the database for repology:

```
psql --username postgres -c "CREATE DATABASE repology"
psql --username postgres -c "CREATE USER repology WITH PASSWORD 'repology'"
psql --username postgres -c "GRANT ALL ON DATABASE repology TO repology"
psql --username postgres --dbname repology -c "CREATE EXTENSION pg_trgm"
psql --username postgres --dbname repology -c "CREATE EXTENSION libversion"
```

in the case you want to change the credentials, don't forget to add
actual ones to `repology.conf`.

Next you can create database schema (tables, indexes etc.) and at the
same time test that the database is accessible with the following command:

```
./repology-update.py --initdb
```

### Fetching/updating repository data

The database is now ready to be filled with data. Typical Repology
update cycle consists of multiple steps, but in most cases you'll need
to just run all of them:

```
./repology-update.py --fetch --fetch --parse --database --postupdate
```

* `--fetch` tells the utility to fetch raw repository data
(download files, scrape websites, clone git repos) into state
directory. Note that it won't refetch (update) data unless
it's specified twice.
* `--parse` enables parsing downloaded data into internal format
which is also saved into state directory.
* `--database` pushes processed package data into the database.
* `--postupdate` runs additional database processing such as
calculating summaries and updating feeds. It's separate from
`--database` because it can be ran in background, parallelly
to the following fetch/update cycle.

### Running the webapp

Repology is a flask application, so as long as you've set up
database and configuration, you may just run the application
locally:

```
./repology-app.py
```

and point your browser to http://127.0.0.1:5000/ to view the
site. This should be enough for personal use, experiments and
testing.

Alternatively, you may deploy the application in numerous ways,
including mod_wsgi, uwsgi, fastcgi and plain CGI application. See
[flask documentation on deployment](http://flask.pocoo.org/docs/deploying/)
for more info.

For instance, you can deploy with `uwsgi` with the following command
line arguments:

```
uwsgi --mount /=repology-app:app --pythonpath=<path-to-repology-checkout>
```

### Link checker

See separate repository https://github.com/repology/repology-linkchecker
