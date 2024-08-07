# Guidance on how to contribute

> All contributions to this project will be released to the public domain.
> By submitting a pull request or filing a bug, issue, or
> feature request, you are agreeing to comply with this waiver of copyright interest.
> Details can be found in our [TERMS](TERMS.md) and [LICENSE](LICENSE).


There are two primary ways to help:
 - Using the issue tracker, and
 - Changing the code-base.


## Using the issue tracker

Use the issue tracker to suggest feature requests, report bugs, and ask questions.
This is also a great way to connect with the developers of the project as well
as others who are interested in this solution.

Use the issue tracker to find ways to contribute. Find a bug or a feature, mention in
the issue that you will take on that effort, then follow the _Changing the code-base_
guidance below.


## Changing the code-base

All new code should have associated unit tests that validate implemented features and the presence or lack of defects.
Additionally, the code should follow any stylistic and architectural guidelines prescribed by the project.
In the absence of such guidelines, mimic the styles and patterns in the existing code-base.

In general, we suggest contributors fork the repository, create a new branch, and submit a
[PR](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests).
This consists of three main steps:

1. Fork, Clone, and Branch (`git` related things)
2. Setup development environment and develop
3. Open a pull request

### Fork, Clone, and Branch

1. [Fork](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo) repository.
   This creates a copy for yourself under your username and is done on GitHub.

2. [Clone](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository) your fork.
   Make a local copy of your fork.

   ```bash
   git clone git@github.com:{{ user.name }}/ngen-cal.git && cd ngen-cal
   ```

3. Create a new branch.
   Open a new branch off of `master` for which you will work

   ```bash
   git checkout -b new_feature_branch
   ```

### Setup development environment and develop

1. Setup and activate python virtual environment

```bash
# Create virtual environment
python -m venv venv
# Activate virtual environment
source ./venv/bin/activate
```

2. Setting up `git` `pre-commit` hooks

[`pre-commit`](https://pre-commit.com/) is used to manage and install `git` `pre-commit` hooks.
`pre-commit` hooks run automatically when `git commit` is invoked and perform checks on the code you are committing.
Example checks are removing trailing white spaces, verifying that large files are not included, or running a code linting tool.
Hooks are configured in the [`.pre-commit-config.yaml`](./.pre-commit-config.yaml) file in the root of the repo.

`pre-commit` can be installed using a package manager (e.g. `brew install pre-commit`) or from `pip` (e.g. `pip install pre-commit`).

Install `pre-commit` hooks into your `git` clone by running:

```bash
pre-commit install
```

Hooks will now run when code is committed.
Alternatively, you can run the pre-commit hooks manually via:

```bash
pre-commit run --all-files
```

For more information, see [`pre-commit`'s documentation](https://pre-commit.com/index.html).

3. Install development version of package(s)

```bash
# installing ngen.cal
pip install -e 'python/ngen_cal[develop]'

# installing ngen.config
pip install -e 'python/ngen_conf[develop]'

# installing ngen.init_config
pip install -e 'python/ngen_init_config[develop]'

# installing ngen.config_gen
pip install -e 'python/ngen_config_gen[develop]'
```

3. Develop

We recommend commit messages follow
[conventional commits](https://www.conventionalcommits.org/en/v1.0.0/#summary)
style.
This is not a requirement, but adherence is appreciated :).


### Open A Pull Request

After pushing changes to your fork you are ready to start the PR process!
First time submitters may find
[this](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork)
guide helpful.

Before you submit a pull request, please verify that you meet the guidelines outlined in
[`PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md).
Additionally, the following guidelines should also be met:

1. If the pull request introduces code or changes to existing code, tests should be included.
   Tests should be written so they are runnable by `pytest`.
   It is recommended that first time submitters view existing tests to get started.
2. Pull requests must pass all GitHub Actions.
3. Usage of non-standard python packages should be kept to a minimum.
