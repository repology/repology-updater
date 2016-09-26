# Repology

![Example report](docs/screenshot.png)

Repology analyzes multiple package repositories and compares versions
of a packages in them.

The report it produces shows which repositories contain or lack
which packages, and whether packages need updating.

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

## Status

Currently the project is most usable as standalone python script
which generates HTML reports.

There is a prototype [repology.org](repology.org) website running
which regularly generates a new report (which is several megabytes
large and may freeze your browser, beware), but running the script
by hand allows multiple filtering options which make the result
much more useful.

## Howto

### Dependencies:

- python3
- pyyaml
- setuptools
- jinja2
- wget (for fetching some repository data)
- git (for fetching some repository data)

### Invocation:

```
./repology.py output.html
```

Will download data for supported repositories and generate HTML
report, writing it into ```output.html```. By default, it includes
all packages, so you may need some filtering:

- ```-m``` filter by maintainer (e.g. ```amdmi3@FreeBSD.org```)
- ```-c``` filter by category (e.g. ```games```; note that this
	       matches substring, e.g. ```games-action``` from Gentoo
	       as well)
- ```-n``` filter only packages present in this many repos
- ```-r``` matches only packages present in specified repo
- ```-R``` matches only packages not present in specified repo

Additionally, you will likely need

- ```-U``` do not update repository information (saves time on
            subsequent runs)

### Examples:

Packages which likely are needed to be added to pkgsrc (because
all other repositories have them) and their versions:

```
./repology.py -U -R pkgsrc -n 3 missing-pkgsrc.html
```

State of FreeBSD ports maintained by me:

```
./repology.py -U -m amdmi3@FreeBSD.org -r FreeBSD maintainer-amdmi3.html
```

State of games along all repos, with irrelevant packages filtered out:

```
./repology.py -U -c games -n 2 games.html
```

## Repository support

### FreeBSD

Links:
- [FreshPorts](http://freshports.org)
- [SVN](https://svnweb.freebsd.org/ports/head)

Parses INDEX-11.bz2 file, available data:
- name
- version
- comment
- maintainer
- category

TODO: Parsing port Makefiles may extract additional info such as
licenses and options.

### Debian/Ubuntu

Links:
- [https://www.debian.org/distrib/packages#search_packages](Debian Packages)
- [http://packages.ubuntu.com/](Ubuntu Packages)

Parses Sources.gz, available data:
- name
- version
- maintainer
- category
- homepage

TODO: May need to parse ```*.debian.tar.xz``` for additional info for
each package. Heavy?

### Gentoo

Links:
- [Gentoo packages](https://packages.gentoo.org/)

Parses git mirror of portage repository (file tree only, doesn't
look into ebuilds), available data:
- name
- version
- category

TODO: Parse metadata.xml for maintainer. Parse ebuilds for more info.

### pkgsrc

Links:
- [pkgsrc.org](http://pkgsrc.org/)
- [CVS](http://cvsweb.netbsd.org/bsdweb.cgi/pkgsrc/)
- [pkgsrc.se](http://www.pkgsrc.se/)

Is capable of generating INDEX file similar to that of FreeBSD, but
it takes too much time (hours). For now, we parse README-all list
from NetBSD, which only contains:
- name
- version
- category
- comment

TODO: Generate and parse INDEX, even if it's done infrequently.

### OpenBSD

- [CVS](http://cvsweb.openbsd.org/cgi-bin/cvsweb/ports/)
- [openports.se](http://openports.se/)

Parses INDEX file (format similar to FreeBSD), available data:
- name
- version
- comment
- maintainer
- category

### Arch

- [Package Search](https://www.archlinux.org/packages/)

Parses package databases (core, extra, community), available data:
- name
- version
- comment
- homepage
- maintainer (packager, actually)
- license

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
