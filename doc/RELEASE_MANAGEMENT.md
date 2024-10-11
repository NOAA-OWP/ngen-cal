# Release Management

The page discusses the release process for official versions of _ngen-cal_.  This process is very much interrelated to the repo branching management model, as discussed in detail on the [GIT_USAGE](./GIT_USAGE.md) doc.

Also, while similar to other OWP repositories, there are several subtle but significant differences here compared to those other repos, due to _ngen-cal_ consisting of several independently-versioned Python packages.  Take care to review the details below fully before releasing a new version.

# The Release Process

## TL;DR

The release process can be summarized fairly simply:
- A release candidate branch is created
- Version numbers are updated as needed for the Python packages
- Testing, QA, and fixes are done on the release candidate branch
- Once the release candidate is ready, changes are integrated into `production` and `master`, and package version tags are created

## Process Steps

[comment]: <> (TODO: Document release manual testing and QA procedures)
[//]: # (TODO: document testing and quality checks/process for release candidate prior to release)
[//]: # (TODO: document peer review and integration process for bug fixes, doc updates, etc., into release candidate branch prior to release (i.e, regular PR?)

[//]: # (TODO: need some kind of check to keep package versions from being incremented except during release process)


1. A release candidate branch, based on `master`, is created in the official OWP repo
    - The name of this branch should be prefixed with either `release-` or `rc-`
    - The name should end with a date string fo the day of creation, in the format `YYYYMMDD`
    - E.g., branch name `release-20241004`
2. Versions are [incremented appropriately](#individual-package-version-rules) for Python packages 
   - Any package that has been modified compared to `production` should have its version incremented
   - Each package has its version set within its `_version.py` file
   - Internal dependency relationships between the packages may also need to be incremented
     - Defined in `setup.cfg` and/or `pyproject.toml` files
   - Changes to reflect version updates are committed and pushed immediately to the newly-created release candidate branch
3. All necessary testing and quality pre-release tasks are performed using this release candiate branch
    - **TODO**: to be documented in more detail
4. (If necessary) Bug fixes, documentation updates, and other acceptable, non-feature changes are applied to the release branch
    - Such changes should go through some peer review process before inclusion in the official OWP branch (e.g., PRs, out-of-band code reviews, etc.)
    - **TODO**: process to be decided upon and documented
5. Steps 3. and 4. are repeated as needed until testing, quality checks, etc. in Step 3. do not require another iteration of Step 4.
    - At this point, the branch is ready for official release
6. All changes in the release candidate branch are incorporated into `production` in the official OWP repo
    - Note that **rebasing** should be used to reconcile changes ([see here](../CONTRIBUTING.md#a-rebase-strategy) for more info)
7. The subsequent `HEAD` commit of `production` is tagged appropriately in the official OWP repo, with [applicable tags for all the nested Python packages that had their version incremented](#tracking-released-versions-for-packages)
8. All changes in the release candidate branch are incorporated back into `master` in the official OWP repo
    - This will include things like bug fixes committed to the release candidate branch after it was branched from `master`
    - As with `production` in Step 6., this should be [done using rebasing](../CONTRIBUTING.md#a-rebase-strategy)
9. The release candidate branch is deleted from the OWP repo (and, ideally, other clones and forks)

# Versioning

## Per-Package

The versioning for ngen-cal is a little different than most OWP repos.

The repository contains the source code of several independently-versioned Python packages.  This includes the "main" `ngen.cal` Python package, but also others such as the `ngen.config_gen` pacakge.  As long as their code remains organized as multiple separate packages, the package versions for these need to be maintained individually.

### Individual Package Version Rules

The individual versioning of the nested packages within the repository should follow [Semantic Versioning](https://semver.org/).  For officially released versions, this means the typical `MAJOR.MINOR.PATCH` pattern.

### Development Versions

During development, it may be convenient or even necessary to increment the version of some package before it is time to go through the release process.  Per the [applicable rule in Semantic Versioning](https://semver.org/#spec-item-9), such versions should follow the pattern of suffixing a hyphen and then some identifier; e.g., `0.5.0-alpha.1`.

Development versions should be used if it becomes necessary to track transitive modifications to a package because of internal dependencies.  If a package (the _dependency_) receives development modifications, and if there is some other package (the _dependent_) using the _dependency_ that strictly requires those modifications to the _dependency_, then a development version should be applied to the _dependency_ and reflected by the dependency definitions of the _dependent_.


## Tracking Released Versions for Packages

Since _ngen-cal_ does not (currently) have a distinct versioning scheme at the repository level, new releases are thought of as composed of new versions of one or more of the nested Python packages.  Because of this, version tags are applied to the repo that are specific to both an updated package and that package's new version, following the pattern `<package_name>/v<pacakge_version>`; e.g., `ngen.cal/v0.3.0`  

Put another way, for every nested Python package _PKG_, and for the package version _VER_ of _PKG_ present in the source code according to the `HEAD` commit of the `production` branch, a tag named "*PKG*/v*VER*" should exist pointing to a commit in the history of `production`; if it does not - in particular, whenever `HEAD` is changed - such a tag should be applied to the `HEAD` of `production`.

For example, when it is time for a new official release, if only the `ngen.cal` and `ngen.init_config` Python packages are changed since the previous release process, then only those packages will have different versions:  say, `0.3.0` and `0.1.0` respectively.  After changes in the release candidate branch are merged to `production`, the `HEAD` of `production` should be tagged with:

* `ngen.cal/v0.3.0`
* `ngen.init_config/v0.1.0`

