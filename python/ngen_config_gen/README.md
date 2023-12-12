# `ngen.config_gen`

`ngen.config_gen` provides a library and framework for generating
NextGen
_[BMI](https://github.com/NOAA-OWP/ngen/wiki/Formulations-and-BMI#bmi-models) model_
configuration files.

## Getting Started

### Installation

In accordance with the python community, we support and advise the usage of virtual environments in any workflow using python.
The following guide uses python's built-in `venv` module to create a  virtual environment.
Note, this personal preference, any python virtual environment manager should work just fine (`conda`, `pipenv`, etc. ).

```bash
# Create and activate python environment, requires python >= 3.8
python -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Install `ngen.config_gen`
pip install 'git+https://github.com/noaa-owp/ngen-cal@master#egg=ngen_config_gen&subdirectory=python/ngen_config_gen'
```

### Simple Usage

`ngen.config_gen` is designed to fit into your workflow, not the other way around.
The following code snippet generates configuration files for the OWP maintained
[`Pet`](https://github.com/NOAA-OWP/evapotranspiration)
and
[`CFE`](https://github.com/noaa-owp/cfe)
modules for all catchments in the 9th HUC2 region.
Changing the `hf_file` and `hf_lnk_file` variables to a different HUC2 region to generate configuration files for that region.
Likewise, filter the `hf` and `hf_lnk_data` DataFrames to only generate configuration files for your region of interest.

See [examples](./examples/) for other workflow examples.

> [!TIP]
> Urls to hydrofabric data are used in the below example for ease, but in our experience local files are magnitudes faster!

```python
import geopandas as gpd
import pandas as pd

from ngen.config_gen.file_writer import DefaultFileWriter
from ngen.config_gen.hook_providers import DefaultHookProvider
from ngen.config_gen.generate import generate_configs

from ngen.config_gen.models.cfe import Cfe
from ngen.config_gen.models.pet import Pet

# or pass local file paths instead
hf_file = "https://lynker-spatial.s3.amazonaws.com/v20.1/gpkg/nextgen_09.gpkg"
hf_lnk_file = "https://lynker-spatial.s3.amazonaws.com/v20.1/model_attributes/nextgen_09.parquet"

hf: gpd.GeoDataFrame = gpd.read_file(hf_file, layer="divides")
hf_lnk_data: pd.DataFrame = pd.read_parquet(hf_lnk_file)

hook_provider = DefaultHookProvider(hf=hf, hf_lnk_data=hf_lnk_data)
# files will be written to ./config
file_writer = DefaultFileWriter("./config/")

generate_configs(
    hook_providers=hook_provider,
    hook_objects=[Cfe, Pet],
    file_writer=file_writer,
)

```

## Related Projects

[`ngen.config`](https://github.com/NOAA-OWP/ngen-cal/tree/master/python/ngen_conf):
Validate and programmatically interacting with
[NextGen](https://github.com/noaa-owp/ngen)
_realization_ configuration files.

[`ngen.init_config`](https://github.com/NOAA-OWP/ngen-cal/tree/master/python/ngen_init_config):
Library used to define BMI model configuration file formats.
Serialize, Deserialize, and validate common configuration formats (i.e. `json`, `yaml`, `toml`, `namelist`).

[`ngen.cal`](https://github.com/NOAA-OWP/ngen-cal/tree/master/python/ngen_cal):
Library and cli tool for calibrating
[NextGen](https://github.com/noaa-owp/ngen)
Model formulations.

[`troute.config`](https://github.com/NOAA-OWP/t-route/tree/master/src/troute-config):
Validate and programmatically interacting with
[t-route](https://github.com/noaa-owp/t-route)
_realization_ configuration files.

## Core Concepts

The goal of `ngen.config_gen` is to provide a framework for creating model configuration files.
All model configuration files are made up of data.
Often this data comes from a variety of "sources".
For example, there may be fields like catchment centroid or wind speed measurement height that could be sourced from geographic data (think the
[hydrofabric](https://github.com/noaa-owp/hydrofabric)
) or the metadata of whatever forcing product will be used for the simulation.
In both instances, the hydrofabric data and the forcing metadata are _sources_ of information that can be used to fill model configuration fields.
There may also be fields like start and end time that are specific to a given simulation, but may be _sourced_ from other kinds of _sources_ think a command line argument or a separate configuration file like a
[NextGen](https://github.com/noaa-owp/ngen)
realization config.

`ngen.config_gen` introduces three concepts _hooks_, a _visitable_, and a _builder_.
These three concepts are used by `ngen.config_gen` to generate new and existing model configuration files.
To start, lets remind ourselves what is needed to generate a model's configuration file.

1. A data model or schema of a model's _catchment specific_ configuration file.
   This is accomplished by defining `pydantic.BaseModel`
   or
   [`ngen.init_config`](https://github.com/NOAA-OWP/ngen-cal/tree/master/python/ngen_init_config)
   subclasses that capture the fields and types of a model's configuration file.
   See
   [`ngen.config.init_config`](https://github.com/NOAA-OWP/ngen-cal/tree/master/python/ngen_conf/src/ngen/config/init_config)
   for implementations of OWP maintained BMI model configuration data models.
2. Data that can be used to build an instance of the model's configuration file.
   Data sufficient to create an instance could come from one or a variety of sources.
   Likewise, some configuration fields might have default values while other may need to be user specified.

Given these observations and assuming that a configuration data model mentioned in 1. has been created,
to generate a model's configuration file using `ngen.config_gen` it is necessary to know:

2.1. What data sources does `ngen.config_gen` provide?
2.2. How does a model tell `ngen.config_gen` what data sources are needed?
2.3. How does a model produce a built configuration file?

As previously stated, this module introduces three concepts _hooks_, a _visitable_, and a _builder_.

_hooks_ are interfaces (python protocol) that a *provide* data to a class instance.
The *provided* data can then be used by the class instance to build up a configuration file
(e.g.  `pydantic.BaseModel` or `ngen.init_config` subclass).
Provided hooks are:
- [`hydrofabric_hook`](https://github.com/noaa-owp/ngen-cal/blob/master/python/ngen_config_gen/src/ngen/config_gen/hooks.py#L119)
- [`hydrofabric_linked_data_hook`](https://github.com/noaa-owp/ngen-cal/blob/master/python/ngen_config_gen/src/ngen/config_gen/hooks.py#L177)

A
[_visitable_](https://github.com/noaa-owp/ngen-cal/blob/master/python/ngen_config_gen/src/ngen/config_gen/hooks.py#L72)
is a thin interface (python protocol) with a single `visit` method.
The `visit` method that takes in a `HookProvider` parameters which has methods that *provide* data for a given hook.
For example, if a class implements the `hydrofabric_hook` method, in the class's `visit` method it would
pass an instance of it`self` to the `hook_provider`'s `provide_hydrofabric_data` method
(e.g. `hook_provider.provide_hydrofabric_data(self)`).
The `HookProvider` would then call the `hydrofabric_hook` method on the instance of the class
*providing* all the necessary data to satisfy that hook.
This pattern is commonly called the visitor pattern.

A
[_builder_](https://github.com/noaa-owp/ngen-cal/blob/master/python/ngen_config_gen/src/ngen/config_gen/hooks.py#L63)
is a thin interface (python protocol) with a single `build` method.
The `build` method takes no parameters other than `self` and when called produces a built configuration file.

Mapping the concepts this modules introduces onto the previously stated questions:

2.1. What data sources does `ngen.config_gen` provide?
    Whatever _hooks_ `ngen.config_gen` defines
2.2. How does a model tell `ngen.config_gen` what data sources are needed?
    By implementing _hook_ methods on a class and calling the associated `HookProvider` method in its `visit` method.
2.3. How does a model produce a built configuration file?
    By implementing a `build` method that returns a build instance of the model's configuration file.

## Roadmap

- [ ] Add support for
[Soil Freeze Thaw](https://github.com/NOAA-OWP/SoilFreezeThaw),
[Soil Moisture Profile](https://github.com/noaa-owp/soilMoistureProfiles/),
[TOPMODEL](https://github.com/NOAA-OWP/topmodel),
[LGAR](https://github.com/NOAA-OWP/LGAR-C),
[SAC-SMA](https://github.com/NOAA-OWP/sac-sma),
and
[LSTM](https://github.com/NOAA-OWP/LSTM)
models
- [ ] Develop command line utility for generating BMI model configuration files.
