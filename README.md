# NGen Calibration

**Description**:  Supporting code/workflows for automated calibration of [NGen](https://github.com/noaa-owp/ngen) Formulations using Dynamic Dimensioned Search (DDS)

  - **Technology stack**: Python based workflow for generating [NGen](https://github.com/noaa-owp/ngen) parameter formulation permutations and running these through the [NGen](https://github.com/noaa-owp/ngen) framework driver.
  - **Status**:  This work is in pre-release development, for more details see the [CHANGELOG](CHANGELOG.md).

## Dependencies

Unit testing done with [pytest](https://github.com/pytest-dev/pytest).  See [requirements.txt](requirements.txt) for other specific python dependencies.

## Installation

`TODO` [INSTALL](INSTALL.md) document.

## Configuration

`TODO`

## Usage

`TODO`

## How to test the software


Install `pytest` and other python dependencies (`pip install -r python/requirements.txt`)
Or create a virtual environment:
```
mkdir venv
virtualenv ./venv
source ./venv/bin/activate
pip install -r python/requirements.txt
```
Then use `pytest` to run the tests:
`pytest --log-cli-level 0 python/ngen-cal/test/`
## Known issues
## Known issues


## Getting help

If you have questions, concerns, bug reports, etc, please file an issue in this repository's Issue Tracker.

## Getting involved

See [CONTRIBUTING](CONTRIBUTING.md), or open an issue to start a conversation!
----

## Open source licensing info
1. [TERMS](TERMS.md)
2. [LICENSE](LICENSE)


----
