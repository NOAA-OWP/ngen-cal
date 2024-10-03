# Release Management

The page discusses the release process for official versions of _ngen-cal_.  This process is very much interrelated to the repo branching management model, as discussed in detail on the [GIT_USAGE](./GIT_USAGE.md) doc.

# The Release Process

## TL;DR

The release process can be summarized fairly simply:
- A version name is finalized
- A release candidate branch is created
- Testing, QA, fixes are done on the release candidate branch
- Once release candidate is ready, changes are integrated into `production` and `master`, and the new version is tagged

## Process Steps

[comment]: <> (TODO: Document release manual testing and QA procedures)
[//]: # (TODO: document testing and quality checks/process for release candidate prior to release)
[//]: # (TODO: document peer review and integration process for bug fixes, doc updates, etc., into release candidate branch prior to release (i.e, regular PR?)

1. The next version name/number is decided/finalized
2. A release candidate branch, based on `master`, is created in the official OWP repo
    - The name of this branch will be `release-X` for version `X`
3. All necessary testing and quality pre-release tasks are performed using this release candiate branch
    - **TODO**: to be documented in more detail
4. (If necessary) Bug fixes, documentation updates, and other acceptable, non-feature changes are applied to the release branch
    - Such changes should go through some peer review process before inclusion in the official OWP branch (e.g., PRs, out-of-band code reviews, etc.)
    - **TODO**: process to be decided upon and documented
5. Steps 3. and 4. are repeated as needed until testing, quality checks, etc. in Step 3. do not require another iteration of Step 4.
    - At this point, the branch is ready for official release
6. All changes in the release candidate branch are incorporated into `production` in the official OWP repo
    - Note that **rebasing** should be used to reconcile changes ([see here](../CONTRIBUTING.md#a-rebase-strategy) for more info)
7. The subsequent `HEAD` commit of `production` is tagged with the new repository version in the official OWP repo
8. All changes in the release candidate branch are incorporated back into `master` in the official OWP repo
    - This will include things like bug fixes committed to `release-X` after it was branched from `master`
    - As with `production` in Step 6., this should be [done using rebasing](../CONTRIBUTING.md#a-rebase-strategy)
9. The release candidate branch is deleted from the OWP repo (and, ideally, other clones and forks)
10. [Additional tags](#extra-package-specific-tags) to help mark release points of the individual nested packages are applied as needed to the `HEAD` commit of `production` in the official OWP repo

# Versions

The versioning for ngen-cal is a little complicated.

The repository contains the sources of several independently-versioned Python packages; e.g., `ngen.cal:0.2.2`, `ngen.config_gen:0.0.2`, etc.  As long as this code remains organized as multiple separate packages, the package versions need to be maintained individually.  Similarly, the repository version as a whole can't simply mirror the version of one of the nest packages:  this could not represent a new version of the repo _without_ any changes to the mirrored package. 

## Rules for Repository Versioning

The solution is for repository versions to be a composite of the [versions of the nested Python packages](#rules-for-individual-nested-package-versions) using the following pattern:

`<ngen.cal>-<ngen.conf>-<ngen.config_gen>-<ngen.init_config>`

E.g., if the current version of the individual Python packages for a repo version are:

      ngen.cal:0.2.2
      ngen.config:0.0.3
      ngen.config_gen:0.0.2
      ngen.init_config:0.1.0

The correct repository version would be `0.2.2-0.0.3-0.0.2-0.1.0`.

### Extra Package-Specific Tags

Using a version like `0.2.2-0.0.3-0.0.2-0.1.0` is not terribly readable or convenience.  To help to mitigate this, in addition to the version tag, tags reflecting the release point of the individual package versions should be maintained when new repository versions are released.

For example, say the repo version is transitioning from `0.2.2-0.0.3-0.0.2-0.1.0` to version `0.2.2-0.0.4-0.0.3-0.1.0`:

* Prior repository version: `0.2.2-0.0.3-0.0.2-0.1.0`
  * Tags implied to exist after this release:
    * `0.2.2-0.0.3-0.0.2-0.1.0`
    * `ngen.cal:0.2.2`
    * `ngen.config:0.0.3`
    * `ngen.config_gen:0.0.2`
    * `ngen.init_config:0.1.0`
* New repository version: `0.2.2-0.0.4-0.0.3-0.1.0`
  * New tags to apply
    * `0.2.2-0.0.4-0.0.3-0.1.0`
    * `ngen.config:0.0.4`
    * `ngen.config_gen:0.0.3`

This new repository version represents that the nested `ngen.config` and `ngen.config_gen` Python packages were updated, but the code and versions for the `ngen.cal` and `ngen.init_config` packages are unchanged.  Two additional tags should be applied to the same commit as for the new `0.2.2-0.0.4-0.0.3-0.1.0` version, `ngen.config:0.0.4` and `ngen.config_gen:0.0.3`.

However, tags `ngen.cal:0.2.2` and `ngen.init_config:0.1.0` must already exist - they would have either been created when `0.2.2-0.0.3-0.0.2-0.1.0` was released or before that - so they do not need to be created or changed.

## Rules for Individual Nested Package Versions

The nested packages within the repository should follow [Semantic Versioning](https://semver.org/) and its typical `MAJOR.MINOR.PATCH` pattern.
