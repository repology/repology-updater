---
name: New repository request
about: Request Request to add a new repository to Repology
labels: new source
---

<!--
Before submitting the request, please check:

- Requirements for new repositories

    https://repology.org/docs/requirements

- List of already submitted, but rejected repositories

    https://repology.org/docs/not_supported

You may also check existing repository configs to get an idea of
what data is used (or decide submit a pull request instead):

    https://github.com/repology/repology-updater/tree/master/repos.d

Please replace example data with data for your repository below:
-->

**Title**
<!--
Desired human readable title to be shown on the website. Shorter forms preferred.
-->

MyMegaRepo 22.04

**Repository data location(s)**
<!--
Link(s) to machine readable package data (may express multiple links in free form).
-->

- https://mymegarepo.org/22.04/{main,contrib,non-free}/packages.json

**Package links**
<!--
Examples or free form templates of links for individual packages. Link to package recipe is mandatory.
Other useful link types include package page, package related issues, build status or logs.
-->

- **Recipe**: https://github.com/mymygarepo/packages/blob/master/{pkgname}/recipe.json
- Package page: https://mymegarepo.org/packages/{pkgname}/
- Package sources: https://github.com/mymygarepo/packages/tree/master/{pkgname}/
- Issues: https://bugzilla.mymegarepo.org/buglist.cgi?quicksearch={pkgname}
- Build status: https://builder.mymegarepo.org/{pkgname}/status
- Build log: https://builder.mymegarepo.org/{pkgname}/buildlogs/latest

**Additional details**
<!--
- More links, such as distibution/repository homepage or GitHub organization
- Brand color, if any
- EoL date, if applicable
- Contact in case of fetch failures or data problems
- Details on custom data format, if it makes sense
- Any other details
-->

<!--
Template for more entries:

**Title**

**Repository data location(s)**
-->
