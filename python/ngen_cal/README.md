# ngen :: cal
This subpackage provides a library and cli utility calibrating ngen models.

## Installation

In accordance with the python community, we support and advise the usage of virtual environments in
any workflow using python. In the following installation guide, we use python's built-in `venv`
module to create a virtual environment in which the tools will be installed. Note this is just
personal preference, any python virtual environment manager should work just fine (`conda`,
`pipenv`, etc. ).

```bash
# Create and activate python environment, requires python >= 3.7
python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip

# Install
python3 -m pip install "git+https://github.com/noaa-owp/ngen-cal@master#egg=ngen_cal&subdirectory=python/ngen_cal"
```

# TODO document this package
