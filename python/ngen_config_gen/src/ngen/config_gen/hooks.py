from typing import Any, Dict, Protocol, runtime_checkable, TYPE_CHECKING
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
    def visit(self, hook_provider: "HookProvider") -> None:
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
        self, version: str, divide_id: str, data: Dict[str, Any]
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
        self, version: str, divide_id: str, data: Dict[str, Any]
    ) -> None:
        """
        Expect to receive a hydrofabric linked data version, data (see class docs), and the associated divide_id.
        """
        ...
