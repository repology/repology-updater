# Repology rules guide

Repology needs to match related packages in separate repositories
even if these are named differently. For this a set of rules is
maintained.

## Ruleset structure

Rulesets reside in [rules.d](../rules.d) directory.

They are text files in YAML format, which contain a list of rules.
The convention is to keep each rule on one line, group them into
blocks and sort alphabetically within a single block to simplify
ruleset maintanance.

Each rule contains a number of conditions (to check whether it
applies to specific package) and actions (which may change package
properties or affect processing of following rules). By default,
each rule starting from the first one is applied to the specific
package. If a rule matches, the following rules are still applied
(but a rule may terminate this process). Each matching rule sees
changes applied by previos rules.

## Rule example

This simple rule match packages with _etracer_ name and change their
names to _extreme-tuxracer_:

```
- { name: etracer, setname: extreme-tuxracer }
```

## Conditions

### family

Matches repository family. See the [repos.d](../repos.d) directory
for the list of families. You may specify multiple families as an array.

Example:

```
- { family: freebsd, ... }

- { family: [ debian, arch, openbsd ], ... }
```

### category

Matches package category. Note that category is not available for
all repositories and has different meaning in each of them, so it
makes sense to always match this along with ```family```. You may
specify a list of categories.

Example:

```
- { family: freebsd, category: games, ... }

- { family: gentoo, category: [ mail-client, mail-filter, mail-mta ], ... }
```

### name

Simply matches package name. Rule matches for packages with a
specified name.

Example:

```
- { name: firefox, ... }
```

### namepat

Matches package name against a regular expression. Whole
name is matched. May contain captures.

Example:

```
- { name: "swig[0-9]+", ... }
```

### ver

Matches package version.

Example:

```
- { name: firefox, ver: "50.0.1", ... }
```

### verpat
Matches package version name against a regular expression. Whole
version is matched. Note that you need to escape periods which
mean "any symbol" in regular expressions.

Example:

```
- { name: firefox, verpat: "50\\.[0-9]+", ... }

- { name: firefox, verpat: "50\\..*", ... }
```

### wwwpat
Matches package homepage against a regular expression. Note that
unlike namepat and verpat, partial match is allowed here.

Example:

```
- { name: firefox, verpat: "mozilla\\.org", ... }
```

## Actions

### setname

Change the effective name of the package. You may use ```$0``` to
substitude original name or ```$1```, ```$2``` etc. to substitude
contents of captures you've used in ```namepat```. Note that you
don't need to use neither ```name``` nor ```namepat``` for ```$0```
to work, but you must have ```namepat``` with corresponding captures
to use ```$1``` and so on.

Examples:
```
# etracer→extreme-tuxracer
- { name: etracer, setname: extreme-tuxracer }

# aspell-dict-en→aspell-ru, aspell-dict-ru→aspell-ru etc.
- { namepat: "aspell-dict-(.*)", setname: "aspell-$1" }

# all packages in dev-perl gentoo category are prepended perl:
# Locale-Msgfmt→perl:Locale-Msgfmt
- { fanmily: gentoo, category: dev-perl, setname: "perl:$0" }
```

### ignore

Completely ignore package. It will not appear anywhere in repology.

Example:

```
# Fedora-specific packages, will not appear in any other repository,
# so we may just drop them
- { namepat: "fedora-.*", family: [ fedora ], ignore: true }
```

### unignore

Undo ```ignore``` possibly applied by earlier rules.

Example:

```
# F-Droid contains a lot of android-only packages, so ignore
# everything from this repository by default
- { family: fdroid, ignore: true }

# But allow cross-platform packages
- { family: fdroid, name: busybox, unignore: true }
```

### ignorever

Never treat a version from this package as the newest. This is
useful when we know the package version is fake, or transformed
incorrectly, and we don't want it to make actual newest version
in other repos appear as outdated.

Example:

```
# openxcom actual version is 1.0. Don't make fake versions
# like 2015.01.01 or 20150101 appear as newer
- { name: openxcom, verpat: "2015.*", ignorever: true }
```

### unignorever

TODO

### warning

TODO
