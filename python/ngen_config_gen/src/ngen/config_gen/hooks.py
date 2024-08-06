"""
This module introduces three concepts _hooks_, a _visitable_, and a _builder_.
These three concepts are used by `ngen.config_gen` to generate new and existing model configuration files.
To start, lets remind ourselves what is needed to generate a model's configuration file.

1. A data model or schema of a model's _catchment specific_ configuration file.
   This is accomplished by defining `pydantic.BaseModel` or `ngen.init_config` subclasses that capture the
   fields and types of a model's configuration file.
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
- `hydrofabric_hook`
- `hydrofabric_linked_data_hook`

A _visitable_ is a thin interface (python protocol) with a single `visit` method.
The `visit` method that takes in a `HookProvider` parameters which has methods that *provide* data for a given hook.
For example, if a class implements the `hydrofabric_hook` method, in the class's `visit` method it would
pass an instance of it`self` to the `hook_provider`'s `provide_hydrofabric_data` method
(e.g. `hook_provider.provide_hydrofabric_data(self)`).
The `HookProvider` would then call the `hydrofabric_hook` method on the instance of the class
*providing* all the necessary data to satisfy that hook.
This pattern is commonly called the visitor pattern.

A _builder_ is a thin interface (python protocol) with a single `build` method.
The `build` method takes no parameters other than `self` and when called produces a built configuration file.

Mapping the concepts this modules introduces onto the previously stated questions:

2.1. What data sources does `ngen.config_gen` provide?
    Whatever _hooks_ `ngen.config_gen` defines
2.2. How does a model tell `ngen.config_gen` what data sources are needed?
    By implementing _hook_ methods on a class and calling the associated `HookProvider` method in its `visit` method.
2.3. How does a model produce a built configuration file?
    By implementing a `build` method that returns a build instance of the model's configuration file.

For a more hands on experience, see example implementations:
https://github.com/NOAA-OWP/ngen-cal/tree/master/python/ngen_config_gen/examples
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable, TYPE_CHECKING
from pydantic import BaseModel

if TYPE_CHECKING:
    # avoid circular import
    from .hook_providers import HookProvider


@runtime_checkable
class Builder(Protocol):
    def build(self) -> BaseModel:
        """
        Return an instance of a model's configuration.
        """
        ...


@runtime_checkable
class Visitable(Protocol):
    def visit(self, hook_provider: HookProvider) -> None:
        """
        Classes that implement `visit` are assumed to also implement some or all hook methods (e.g. `hydrofabric_hook`).
        Classes that implement `visit` should call associated hook provider methods for each hook
        they implement passing `self` as the argument. For example, if class C implements `visit`
        and `hydrofabric_hook` C's visit method could be defined as:

        ```
        class C:
            def visit(self, hook_provider: "HookProvider") -> None:
                hook_provider.provide_hydrofabric_data(self)

            def hydrofabric_hook(
                self, version: str, divide_id: str, data: Dict[str, Any]
            ) -> None:
                # do things
        ```
        """
        ...


@runtime_checkable
class BuilderVisitable(Builder, Visitable, Protocol):
    """
    Convenance protocol / interface that enables `isinstance` checking some object instance to
    determine if it implements `build` and `visit` methods.
    """

    ...


@runtime_checkable
class HydrofabricHook(Protocol):
    """
    v2.0 Hydrofabric data schema:
        divide_id                     str
        areasqkm                    float
        toid                          str
        type                          str
        ds_id                       float
        id                            str
        lengthkm                    float
        tot_drainage_areasqkm       float
        has_flowline                 bool
        geometry                 geometry
    """

    def hydrofabric_hook(
        self, version: str, divide_id: str, data: dict[str, Any]
    ) -> None:
        """
        Expect to receive a hydrofabric version, data (see class docs), and the associated divide_id.
        """
        ...


@runtime_checkable
class HydrofabricLinkedDataHook(Protocol):
    """
    v2.0 Hydrofabric linked data schema:
        divide_id                        str
        elevation_mean                 float
        slope_mean                     float
        impervious_mean                float
        aspect_c_mean                  float
        twi_dist_4                       str
        X                              float
        Y                              float
        gw_Coeff                       float
        gw_Zmax                        float
        gw_Expon                       float
        bexp_soil_layers_stag=1        float
        bexp_soil_layers_stag=2        float
        bexp_soil_layers_stag=3        float
        bexp_soil_layers_stag=4        float
        ISLTYP                           int
        IVGTYP                           int
        dksat_soil_layers_stag=1       float
        dksat_soil_layers_stag=2       float
        dksat_soil_layers_stag=3       float
        dksat_soil_layers_stag=4       float
        psisat_soil_layers_stag=1      float
        psisat_soil_layers_stag=2      float
        psisat_soil_layers_stag=3      float
        psisat_soil_layers_stag=4      float
        cwpvt                          float
        mfsno                          float
        mp                             float
        quartz_soil_layers_stag=1      float
        quartz_soil_layers_stag=2      float
        quartz_soil_layers_stag=3      float
        quartz_soil_layers_stag=4      float
        refkdt                         float
        slope                          float
        smcmax_soil_layers_stag=1      float
        smcmax_soil_layers_stag=2      float
        smcmax_soil_layers_stag=3      float
        smcmax_soil_layers_stag=4      float
        smcwlt_soil_layers_stag=1      float
        smcwlt_soil_layers_stag=2      float
        smcwlt_soil_layers_stag=3      float
        smcwlt_soil_layers_stag=4      float
        vcmx25                         float
    """

    def hydrofabric_linked_data_hook(
        self, version: str, divide_id: str, data: dict[str, Any]
    ) -> None:
        """
        Expect to receive a hydrofabric linked data version, data (see class docs), and the associated divide_id.
        """
        ...
