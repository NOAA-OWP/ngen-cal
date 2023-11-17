# TODO: check when runtime_checkable was introduced
from typing import Any, Dict, Protocol, runtime_checkable, TYPE_CHECKING
from pydantic import BaseModel

if TYPE_CHECKING:
    # avoid circular import
    from .hook_providers import HookProvider


@runtime_checkable
class Builder(Protocol):
    def build(self) -> BaseModel:
        ...


@runtime_checkable
class Visitable(Protocol):
    def visit(self, hook_provider: "HookProvider") -> None:
        ...


@runtime_checkable
class BuilderVisitable(Builder, Visitable, Protocol):
    pass


# TODO: determine if this is an appropriate name. See what id's are referenced
# in the linked data (divides id?)
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
        ...


# TODO: determine if this is an appropriate name. See what id's are referenced
# in the linked data (divides id?)
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
        ...
