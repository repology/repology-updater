# Running repology

## Dependencies

Needed for core:

- [Python](https://www.python.org/) 3.6+
- Python module [pyyaml](http://pyyaml.org/)
- Python module [requests](http://python-requests.org/)
- [libversion](https://github.com/repology/libversion) library

Needed for fetching/parsing specific repository data:

- Python module [rubymarshal](https://github.com/d9pouces/RubyMarshal)
- Python module [lxml](http://lxml.de/)
- [wget](https://www.gnu.org/software/wget/)
- [git](https://git-scm.com/)
- [rsync](https://rsync.samba.org/)
- [librpm](http://www.rpm.org/) and [pkg-config](https://www.freedesktop.org/wiki/Software/pkg-config/)
- [tclsh](https://www.tcl.tk/) and [tcllib](https://www.tcl.tk/)

Needed for web-application:

- Python module [flask](http://flask.pocoo.org/)
- Python module [psycopg](http://initd.org/psycopg/)
- [PostgreSQL database](https://www.postgresql.org/) 9.6+

Optional, for doing HTML validation when running tests:
- Python module [pytidylib](https://pypi.python.org/pypi/pytidylib) and [tidy-html5](http://www.html-tidy.org/) library

Optional, for checking schemas of configuration files:
- Python module [voluptuous](https://pypi.python.org/pypi/voluptuous)

Optional, for python code linding:
- Python module [flake8](https://pypi.python.org/pypi/flake8)
- Python module [flake8-buildins](https://pypi.python.org/pypi/flake8-builtins)
- Python module [flake8-import-order](https://pypi.python.org/pypi/flake8-import-order)
- Python module [flake8-quotes](https://pypi.python.org/pypi/flake8-quotes)

## Building

Though repology is mostly a Python project, it contains C utility to
read binary rpm format, which is used for parsing ALT Sisyphus
repository. To build the utility, run ```make``` in project root.
You need librpm and pkg-config.

## Usage

### Configuration

First, you may need to tune settings which are shared by all repology
utilities, such as directory for storing downloaded repository state
or DSN (string which specifies how to connect to PostgreSQL database).
See ```repology.conf.default``` for default values, create
```repology.conf``` in the same directory to override them or
specify path to alternative config in ```REPOLOGY_SETTINGS```
environment variable, or override settings via command line.

By default, repology uses ```./_state``` state directory and
```repology/repology/repology``` database/user/password on localhost.

### Fetching/updating repository data

First, let's try to fetch some repository data and see if it works.
No database is needed at this point.

```
./repology-update.py --fetch --parse
```

* ```--fetch``` tells the utility to fetch raw repository data
(download files, scrape websites, clone git repos) into state
directory. Note that it won't refetch (update) data unless
```--update``` is also specified.
* ```--parse``` parses downloaded raw data into internal format
which is also saved into state directory.

After data is downloaded you may inspect it with

```
./repology-dump.py | less
```

The utility allows filtering and several modes of operation, see
```--help``` for full list of options.

### Creating the database

To run repology webapp you need a PostgreSQL database.

First, ensure PostgreSQL server is installed and running,
then execute the following commands to create a database for
repology:

```
psql --username postgres -c "CREATE DATABASE repology"
psql --username postgres -c "CREATE USER repology WITH PASSWORD 'repology'"
psql --username postgres -c "GRANT ALL ON DATABASE repology TO repology"
psql --username postgres --dbname repology -c "CREATE EXTENSION pg_trgm"
```

now you can create database schema (tables, indexes etc.) with:

```
./repology-update.py --initdb
```

and finally push parsed data into the database with:

```
./repology-update.py --database
```

### Running the webapp

Repology is a flask application, so as long as you've set up
database and configuration, you may just run the application
locally:

```
./repology-app.py
```

and point your browser to http://127.0.0.1:5000/ to view the
site. This should be enough for personal usage, experiments and
testing.

Alternatively, you may deploy the application in numerous ways,
including mod_wsgi, uwsgi, fastcgi and plain CGI application. See
[flask documentation on deployment](http://flask.pocoo.org/docs/deploying/)
for more info.

### Keeping up to date

To keep repository data up to date, you'll need to periodically
refetch it and update the database. Note there's no need to recreate
database schema every time (unless it needs changing). Everything
can be done with single command:

```
./repology-update.py --fetch --update --parse --database
```

### Link checker

A separate utility exists to gather and refresh availability information
for links (homepages and downloads) extracted by repology. After updating
the database once, you may run

```
./repology-linkchecker.py
```

This will issue a HEAD (and if that fails, a GET) request for each link,
and save the result (such as HTTP code and redirect information)
in the database.

Note that typical repology installation would know of hundreds of
thousands of links so this may take time. Consult `--help` for a list
of additional options. Typical Repology setup with regular update would
run something like

```
./repology-linkchecker.py --unchecked --jobs 10
```

after each update to handle newly discovered links, and

```
./repology-linkchecker.py --checked --age 7 --jobs 10
```

weekly to refresh information of already known links in background.
