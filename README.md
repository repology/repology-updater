# Repology

[![Build Status](https://travis-ci.org/AMDmi3/repology.svg?branch=master)](https://travis-ci.org/AMDmi3/repology)
[![Coverage Status](https://coveralls.io/repos/github/AMDmi3/repology/badge.svg?branch=master)](https://coveralls.io/github/AMDmi3/repology?branch=master)

![Example report](docs/screenshot.png)

Repology tracks and compares package versions along multiple
repositories including Arch, Chocolatey, Debian, Fedora, FreeBSD,
Gentoo, Mageia, OpenBSD, OpenSUSE, pkgsrc, Sisyphus, SlackBuilds,
Ubuntu and more.

## Uses

- **Users**:
  - Compare completeness and freshness of package repositories,
    choose most up to date distro
  - Find out what repositories contain newest versions of packages
    you need
- **Package/port maintainers**:
  - Another way to track new releases of software you package
  - Compete with other distros in keeping up to date
  - Find fellow maintainers to resolve packaging problems together
  - Keep package naming and versioning schemes in sync to other
    repos for your and your user's convenience
- **Software authors**:
  - Keep track of how well your project is packaged
  - Keep in touch with your product package maintainers
  - If you're not using [semantic versioning](http://semver.org/)
    yet, see how useful it is

# Status

Repology is currently in an early phase of development, with a goal
of creating usable utility in a quick and dirty way. For now, it is
usable in two modes: as a command line generator of single HTML
report and a static website generator for [repology.org](repology.org).

## Howto

### Dependencies

Mandatory:

- [Python](https://www.python.org/) 3.x
- Python module [pyyaml](http://pyyaml.org/)
- Python module [requests](http://python-requests.org/)

Optional, needed for parsing some repositories:

- [wget](https://www.gnu.org/software/wget/)
- [git](https://git-scm.com/)
- [librpm](http://www.rpm.org/) and [pkg-config](https://www.freedesktop.org/wiki/Software/pkg-config/)

Optional, for web-application:

- Python module [flask](http://flask.pocoo.org/)
- Python module [psycopg](http://initd.org/psycopg/)
- [https://www.postgresql.org/](PostgreSQL database) 9.5+

### Building

Though repology is mostly a Python project, it contains C utility to
read binary rpm format, which is used for parsing ALT Sisyphus
repository. To build the utility, run ```make``` in project root.
You need librpm and pkg-config.

### Usage

#### Configuration

First, you may need to tune settings which are shared by all repology
utilities, such as directory for storing downloaded repository state
or DSN (string which specifies how to connect to PostgreSQL database).
See ```repology.conf.default``` for default values, create
```repology.conf``` in the same directory to override them or
specify path to alternative config in ```REPOLOGY_SETTINGS```
environment variable, or override settings via command line.

By default, repology uses ```./_state``` state directory and
```repology/repology/repology``` database/user/password on localhost.

#### Fetching/updating repository data

First, let's try to fetch some repository data and see if it works.
No database is needed at this point.

```
./repology-update --fetch --parse
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

#### Creating the database

To run repology webapp you need PostgreSQL database.

First, ensure PostgreSQL server is installed and running,
and execute the following SQL queries (usually you'll run
```psql -U postgres``` for this):

```
CREATE DATABASE repology;
CREATE USER repology WITH PASSWORD 'repology';
GRANT ALL ON DATABASE repology TO repology;
```

now you can create database schema (tables, indexes etc.) with:

```
./repology-update --initdb
```

and finally push parsed data into the database with:

```
./repology-update --database
```

#### Running the webapp

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
[flask documentation on deployment](http://flask.pocoo.org/docs/0.11/deploying/)
for more info.

#### Keeping up to date

To keep repository data up to date, you'll need to periodically
refetch it and update the database. Note there's no need to recreate
database schema every time (unless it needs changing). Everything
can be done with single command:

```
./repology-app.py --fetch --update --parse --database
```

## Repository support

| Repository                       | Summary | Maint-r | Categ | WWW | License | Download |
|----------------------------------|:-------:|:-------:|:-----:|:---:|:-------:|:--------:|
| ALT Sisyphus                     | ✔       | ✔       | ✔     |     |         |          |
| Arch                             | ✔       | ✔       |       | ✔   | ✔       |          |
| CentOS, Fedora, Mageia, OpenSUSE | ✔       |         | ✔     | ✔   | ✔       |          |
| Chocolatey                       | ✔       |         |       | ✔   |         |          |
| CPAN                             |         | ✔       |       | ✔   |         |          |
| Debian, Ubuntu                   |         | ✔       | ✔     | ✔   |         |          |
| F-Droid                          |         |         | ✔     | ✔   | ✔       |          |
| FreeBSD                          | ✔       | ✔       | ✔     | ✔   |         |          |
| freshcode.club                   | ✔       | n/a     |       | ✔   |         |          |
| Gentoo                           |         | ✔       | ✔     |     |         |          |
| GoboLinux                        | ✔       |         |       | ✔   | ✔       |          |
| OpenBSD                          | ✔       | ✔       | ✔     |     |         |          |
| pkgsrc                           | ✔       | ✔       | ✔     |     |         |          |
| PyPi                             | ✔       |         |       | ✔   |         |          |
| SlackBuilds                      |         | ✔       | ✔     | ✔   |         | ✔        |
| YACP                             |         |         |       |     |         |          |

### FreeBSD

Parses data from INDEX-11.bz2.

TODO: Parsing port Makefiles may extract additional info such as
licenses and options.

Links:
- [FreshPorts](http://freshports.org)
- [SVN](https://svnweb.freebsd.org/ports/head)

### Debian/Ubuntu

Parses data from Sources.gz. Maintainers are taken from both ```Maintainer``` and ```Uploader``` fields.

TODO: May need to parse ```*.debian.tar.xz``` for additional info for
each package. Heavy?

Links:
- [https://www.debian.org/distrib/packages#search_packages](Debian Packages)
- [http://packages.ubuntu.com/](Ubuntu Packages)

### Gentoo

Parses git mirror of portage repository (file tree only, doesn't
look into ebuilds).

TODO: Parse ebuilds for more info.

Links:
- [Gentoo packages](https://packages.gentoo.org/)

### pkgsrc

Parses INDEX file (format similar to FreeBSD).

Lacks maintainer for ~24 ports which use OWNER instead because
OWNER does not get to INDEX.

Links:
- [pkgsrc.org](http://pkgsrc.org/)
- [CVS](http://cvsweb.netbsd.org/bsdweb.cgi/pkgsrc/)
- [pkgsrc.se](http://www.pkgsrc.se/)

### OpenBSD

Parses INDEX file (format similar to FreeBSD).

Links:
- [CVS](http://cvsweb.openbsd.org/cgi-bin/cvsweb/ports/)
- [openports.se](http://openports.se/)

### Arch

Parses package databases (core, extra, community).

Links:
- [Package Search](https://www.archlinux.org/packages/)

### Fedora, Mageia, CentOS, OpenSUSE

Parses source package lists.

Links
- [Fedora Repository](https://mirror.yandex.ru/fedora/linux/development/rawhide/Everything/source/tree/)
- [Fedora Package Database](https://admin.fedoraproject.org/pkgdb)
- [Fedora GIT Repositories](http://pkgs.fedoraproject.org/cgit/rpms/)
- [CentOS Repository](http://vault.centos.org/centos/7/os/Source/)
- [CentOS Packages](http://centos-packages.com/)
- [Mageia Repository](https://mirrors.kernel.org/mageia/distrib/cauldron/SRPMS/core/release/)
- [Mageia App Db](https://madb.mageia.org/)
- [OpenSUSE Repository](http://download.opensuse.org/tumbleweed/repo/src-oss/suse/)
- [OpenSUSE ](https://software.opensuse.org/)

### Sisyphus

Parses srclist.classic files with custom C utility.

Links:
- [Sisyphus repository](http://www.sisyphus.ru/en/)

### Chocolatey

Parses XML descriptions of packages from chocolatey API.

Links:
- [Chocolatey packages](https://chocolatey.org/packages)

### SlackBuilds

Parses .info files from SlackBuilds.

Links:
- [SlackBuilds.org](https://slackbuilds.org/)

### freshcode.club

Parses feed of version updates from freshcode.club.
Since feed only contains 100 latest updates, it is accumulated in
the state file with each update. Entries with highest vesion number
are preserved.

Links:
- [freshcode.club](http://freshcode.club/)

### CPAN

Parses CPAN 02packages.details.txt index.

Links:
- [CPAN](http://search.cpan.org/)

### PyPi

Parses PyPi HTML index.

Links:
- [PyPi](https://pypi.python.org/pypi)

### F-Droid

Parses F-Droid package index XML. Is not enabled yet as most packages
are android-unique, and, even if these are ports of PC software, have
different versioning schemas. Probably it's best to support F-Droid
packages on opt-in basis.

Links:
- [XML index](https://f-droid.org/repo/index.xml)

## Reading the report

Report is HTML table, columns correspond to repositories and rows
correspond to packages. Cells hold package versions, highlighted
as follows:

- ```cyan```: package is only present in a single repo: nothing to
              compare version to, and may be local artifact
- ```green```: package up to date
- ```red```: package outdated (there's newer version in some other repo)
- ```yellow```: there are multiple packages some of which are up to date
                and others are outdated
- ```gray```: version was manually ignored, likely because of broken
              versioning scheme

Note that there may be multiple packages of a same name in a single repo
(either naturally, or because of name transformations).

## Package matching

Some packages are named differently across separate repositories,
so package name transformations are performed to merge differently
named packages into a single entity. [rules.yaml](rules.yaml) contains
rules for such transformation, is in YAML format containing array
of rules. Each rule may contain:

- Matching conditions:
  - ```repo```: only apply rule to repositories of specific type
    (currently ```freebsd```, ```debian```, ```gentoo```, ```pkgsrc```,
     or ```openbsd``` note that these are NOT repository names)
  - ```name```: apply to package of specified name
  - ```namepat```: apply to package with name matching specified regexp
  - ```verpat```: apply to package with version matching specified regexp

- Actions:
  - ```ignore```: completely ignore the package
  - ```setname```: set package name to an argument. ```$0``` is replaced
    with old name, ```$1```, ```$2``` and so on may be used to refer
    capture groups in ```namepat``` regexp, if it's present
  - ```pass```: leave package as is. Useful to prevent following rules
    from matching

Only first matching rule applies. If no rule applies (or ```pass```
rule applies), package data is not modified. Afterwards, regardless
of whether any rule matched, name is always converted to lowercase
and underscores (```_```) replaced with hyphens (```-```).

Note that transformation may merge several packages into single
entry. If they are unrelated this may be a problem (solved by giving
them unique names by rules based on e.g category), otherwise it is
useful and may be done intentionally to merge variants or parts of
specific project into single entity (e.g. merge ```freeciv-client```
and ```freeciv-server``` into ```freeciv``` in pkgsrc, to match
them both against ```freeciv``` in other repos, or match ```fltk15```,
```fltk16```, ```fltk17``` into just ```fltk``` and look at newest
version).

### Example

Debian has ```botan1.10```, FreeBSD has ```botan110``` and other
repos have ```botan```. To merge these into single entity:

```
- { repo: debian, name: botan1.10, setname: botan }
- { repo: freebsd, name: botan110, setname: botan }
```

FreeBSD names Perl module ports as ```p5-My-Module```, Debian does
```libmy-module-perl```, and Gentoo just places ```My-Module``` under
```dev-perl``` category. To merge all these perl modules into single
synthetic ```perl:my-module``` entry (and actually do the same to
all perl modules at once):

```
- { repo: freebsd, namepat: "p5-(.*)",      setname: "perl:$1" }
- { repo: debian,  namepat: "lib(.*)-perl", setname: "perl:$1" }
- { repo: gentoo,  category: dev-perl,      setname: "perl:$0" }
```

## Author

* [Dmitry Marakasov](https://github.com/AMDmi3) <amdmi3@amdmi3.ru>

## License

GPLv3 or later, see [COPYING](COPYING).
