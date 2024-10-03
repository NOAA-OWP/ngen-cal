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

1. The nested Python packages that will be releasing new versions is identified
    - And their new version numbers 
2. A release candidate branch, based on `master`, is created in the official OWP repo
    - The name of this branch should be prefixed with either `release-` or `rc-`
    - The name should also reflect the nested packages that will get new versions and their new version numbers
3. All necessary testing and quality pre-release tasks are performed using this release candiate branch
    - **TODO**: to be documented in more detail
4. (If necessary) Bug fixes, documentation updates, and other acceptable, non-feature changes are applied to the release branch
    - Such changes should go through some peer review process before inclusion in the official OWP branch (e.g., PRs, out-of-band code reviews, etc.)
    - **TODO**: process to be decided upon and documented
5. Steps 3. and 4. are repeated as needed until testing, quality checks, etc. in Step 3. do not require another iteration of Step 4.
    - At this point, the branch is ready for official release
6. All changes in the release candidate branch are incorporated into `production` in the official OWP repo
    - Note that **rebasing** should be used to reconcile changes ([see here](../CONTRIBUTING.md#a-rebase-strategy) for more info)
7. The subsequent `HEAD` commit of `production` is tagged appropriately in the official OWP repo, with [applicable tags for all the nested Python packages that received new versions](#versions)
8. All changes in the release candidate branch are incorporated back into `master` in the official OWP repo
    - This will include things like bug fixes committed to the release candidate branch after it was branched from `master`
    - As with `production` in Step 6., this should be [done using rebasing](../CONTRIBUTING.md#a-rebase-strategy)
9. The release candidate branch is deleted from the OWP repo (and, ideally, other clones and forks)

# Versions

The versioning for ngen-cal is a little different than most OWP repos.

The repository contains the source code of several independently-versioned Python packages.  This includes the "main" `ngen.cal` Python package, but also others such as the `ngen.config_gen` pacakge.  As long as their code remains organized as multiple separate packages, the package versions for these need to be maintained individually.

The individual versioning of the nested packages within the repository should follow [Semantic Versioning](https://semver.org/) and its typical `MAJOR.MINOR.PATCH` pattern.

Since _ngen-cal_ does not (currently) have a distinct versioning scheme at the repository level, new releases are thought of as composed of new versions of one or more of the nested Python packages.  Because of this, version tags are applied to the repo that are specific to both an updated package and that package's new version, following the pattern `<package_name>:<pacakge_version>`.  

Put another way, for every nested Python package `PKG`, and for the package version `VER` of `PKG` present in the source code according to the `HEAD` commit of the `production` branch, a tag named `PKG:VER` must exist pointing to a commit in the history of `production`; if it does not - in particular, whenever `HEAD` is changed - such a tag should be applied to the `HEAD` of `production`.

For example, when it is time for a new official release, if only the `ngen.cal` and `ngen.init_config` Python packages are changed since the previous release process, then only those packages will have different versions:  say, `0.3.0` and `0.1.0` respectively.  After changes in the release candidate branch are merged to `production`, the `HEAD` of `production` should be tagged with:

* `ngen.cal:0.3.0`
* `ngen.init_config:0.1.0`

