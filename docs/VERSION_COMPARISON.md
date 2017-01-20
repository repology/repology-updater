# Repology version comparison algorithm

The core of the project is its version comparison algorithm, which
need to be robust and generic enough to compare versions in different
repos which may have incompatible rules or traditions for mangling.

For example, ```1.2.3alpha4```, ```1.2.3~a4``` and ```1.2.3.a4```
are all the same version written differently, and these should all
compare as equal. And, by the way, it should be compare less to
```1.2.3``` because alpha versions come before the release. Repology
does that.

## Preprocessing

It is worth mentioning that in many cases versions are preprocessed
in repository-specific way. For example, in FreeBSD ports you can
run into something like ```1.2.3_4,5```, which means upstream version
```1.2.3```, port revision 4, epoch 5. Revisions and epochs are internal
to FreeBSD ports, have nothing to do with upstream and cannot be compared
to anything in other repositories (though they have similar concepts). So
such artifacts are just stripped. This doesn't make the life much
easier though, as complexity described in the first example remains.

## Base algorithm

As long as simple numeric versions are used, it is pretty easy to
compare them (so please [DO](http://semver.org/) use these). When
you have two versions, you split them into components by periods,
and just compare them as numbers. If there's different number of
components, the shorter version in padded with zeroes.

```
# components are compared from left to right, e.g
# leftmost components have the highest priority
1.0.0 < 1.0.1 < 1.1.0 < 2.0.0

# numeric comparison, leading zeros do not matter
1.1 == 1.0001

# pad with zeros up to equal component number
1.2.0 == 1.2
1.2 < 1.2.1 < 1.3
```

## Alphabetics handling

The complexity begins when alphabetic part is added. First, some facts:

* Alphabetic version component may be used the same way as numeric ones
  ```1.2.a < 1.2.b < 1.2.e```, ```1.2a < 1.2b```
* Alphabetic suffix may be used to denote minor releases
  ```1.2 < 1.2a < 1.2b```
* Alphabetic part may denote pre-release versions
  ```1.2alpha1 < 1.2alpha2 < 1.2beta1 < 1.2prerelease1 < 1.2```

Let's introduce some assumptions to make life easier:

1. When comparing, alphabetics are compared lexicographically.
   This is obvious for single-letter suffixes, but it's less obvious
   for long words. *Luckily*, the most words (that is, ```alpha```,
   ```beta```, ```prerelease```, and ```rc```) used in versions may
   be compared which each other and produce correct order when
   compared lexicographically.
2. We may trim any alphabetic part to a single letter.
   This follows from 1: ```alpha```, ```beta```, ```prerelease```,
   ```rc``` are compared the same as ```a```, ```b```, ```p```, and
   ```r```, and this is useful because ```a``` and ```alpha``` are
   often used interchangeably in the versions.
3. Case is ignored.
   Well, *luckily* I don't have cases where ```1a``` and ```1A```
   would bean different versions
4. We split all component into parts each of which contains no more
   than a single numeric part and a single alpha part. First, it
   makes further comparison possible, as we don't know how to compare
   complex things. Next, it catches some cases when maintainers
   split upstream versions by hand.
   The split may me done in multiple ways, but we now only split
   ```0a0``` into ```0.a0```, as this is the most common case and
   it is almost unambiguous (e.g. ```1alpha2``` is version one,
   second alpha, not first alpha with subversion two). This does
   not affect comparison of equally formatted versions ```1alpha1
   vs. 1alpha2```, but allows us to catch differently formatted
   versions as well ```1.alpha1``` vs.  ```1alpha2```, which is
   pretty common case.
5. We now only have 4 simple variants of mixing numeric and alpha
   parts:
   * ```0```
   * ```0a```
   * ```a```
   * ```a0```
   What's left is to define comparison rules for these:
6. Letters always compare less to numbers. That is, ```z < 0```.
   This makes ```1.2.alpha1``` come before ```1.2``` and ```1.2.0```
   which is the same. Note that due to rule 4, ```1.2alpha1``` is
   converted to ```1.2.alpha1``` so is treated the same way.
7. Missing subcomponents are always compared before existing ones. E.g.
   ```0``` < ```0a``` (covers letter suffixes for minor releases as in
   ```1.2 < 1.2a < 1.2b```) and ```a``` < ```a0``` (ambiguous, but
   not widely used in practice)

## Algorithm

Summarizing, what our algorithm does is:

1. Split versions into components by any number of non-alphanumerics.
   ```1.2a2-1``` → ```['1', '2a2', '1']```
2. Further split ```0a0``` components
   ```['1', '2a2', '1']``` → ```['1', '2', 'a2', '1']```
3. Each component is converted into internal representation,
   num-alpha-num triple. Empty subcomponents are filled with
   values which always compare less than actual ones (-1 for numbers
   and empty string for strings).
   * ```a``` -> ```(-1, 'a', -1)```
   * ```a2``` -> ```(-1, 'a', 2)```
   * ```2``` -> ```(2, '', -1)```
   * ```2a``` -> ```(2, 'a', -1)```
4. The shorter vector is padded with ```(0, '', -1)``` (representation of zero)
5. Compare from left to right

## Failures

All know theoretical and practical failures of the algorithm will
be listed here. They fall into two major categories: some may be
fixed in the algorithm (and will be, or will be not due to rarity
of occurrences and avoiding adding unneeded complexity), or may not
be fixed, due to lack of information.

* ```1EE2AB3```

  These are undefined behavior now as we assume only one alphabetic
  part. I've seen this in practice for some nethack-related package,
  and this also may be encountered when version contains git commit
  hashes. The former case may be fixed by improving splitting, the
  latter is doomed.

* ```1.0beta``` vs. ```1.0beta1```

  Fails because the former is not split. May be fixed by handling
  words (as opposed to letters) specially. Real-word cases have
  it either split upstream (e.g. ```1.0.beta```), and most cases
  are numbered anyway.

* ```1.beta``` vs. ```1.beta1```

  Compare as less, but may be expected to be equal. May be easily
  fixed, as soon as we assume there can't be ```beta0```.

* ```1.0 vs 1.0patch2```

  ```patch``` is a special word which requires different handling
  than all other alphabetics. While ```1.0alpha1 < 1.0```,
  ```1.0patch1``` > ```1.0```. May handle it (as well as ```p```)
  specially. FreeBSD does that, btw.

There are also cases like ```1b``` vs. ```1.b```, ```1beta vs.
1.beta```, but the cause of this is package maintainer representing version incorrectly.

but this is out of scope of this algorithm.
