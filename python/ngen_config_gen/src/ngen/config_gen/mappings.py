"""
ngen.config_gen.mappings provides Hydrofabric version specific name mappings to
Hydrofabric 2.0 names. Mappings are split up by hook and hf version. For
example, the namespace `LinkedData_2_2` provides mappings _from_ Hydrofabric
2.2 Linked Data (`divide-attributes`) column names to Hydrofabric 2.0 Linked
Data (`model_attributes`) names.

Use ngen.config_gen.mappings to rename pandas DataFrame columns used as input to a
DefaultHookProvider or other HookProviders. This retains compatibility with
existing hook objects and avoids the need to update names referenced in
hook implementations.

See `examples/generate_conus_hf_2_2` for a concrete example.
"""

from __future__ import annotations

import typing
from types import MappingProxyType

from ._class_var_iter import ClassVarIter, pub_cls_vars


class LinkedData_2_2(metaclass=ClassVarIter[typing.Mapping[str, str]]):
    """
    LinkedData_2_2 provides mappings from Hydrofabric 2.2 Linked Data (`divide-attributes`)
    column names to Hydrofabric 2.0 Linked Data (`model_attributes`) names for
    Conus, Alaska, Hawaii, Puerto Rico, and the U.S. Virgin Islands
    Hydrofabric domains.

    Use LinkedData_2_2 to rename pandas DataFrame columns used as input to a
    DefaultHookProvider or other HookProviders. This retains compatibility with
    existing hook objects and avoids the need to update names referenced in
    hook implementations.

    Examples:
      # 1. remap conus HF 2.2 names -> HF 2.0 names
      import geopandas as gpd

      conus_lnk_data = gpd.read_file("conus_nextgen.gpkg", layer="divide-attributes")
      conus_lnk_data = conus.rename(columns=LinkedData_2_2.conus, errors="ignore")

      conus_divides  = gpd.read_file("conus_nextgen.gpkg", layer="divides")
      hook_provider = DefaultHookProvider(hf=conus_divides, hf_lnk_data=conus_lnk_data)

      # 2. blindly try all provided HF 2.2 remappings
      import pandas as pd
      import geopandas as gpd

      def try_all_2_2_remaps(df: pd.DataFrame) -> pd.DataFrame:
          for _, remap in LinkedData_2_2:  # or LinkedData_2_2.items()
              df = df.rename(columns=remap, errors="ignore")
          return df

      hi = gpd.read_file("hi_nextgen.gpkg", layer="divide-attributes")
      hi = try_all_2_2_remaps(hi)
    """

    conus = MappingProxyType(
        {
            "divide_id": "divide_id",
            "mode.bexp_soil_layers_stag=1": "bexp_soil_layers_stag=1",
            "mode.bexp_soil_layers_stag=2": "bexp_soil_layers_stag=2",
            "mode.bexp_soil_layers_stag=3": "bexp_soil_layers_stag=3",
            "mode.bexp_soil_layers_stag=4": "bexp_soil_layers_stag=4",
            "mode.ISLTYP": "ISLTYP",
            "mode.IVGTYP": "IVGTYP",
            "geom_mean.dksat_soil_layers_stag=1": "dksat_soil_layers_stag=1",
            "geom_mean.dksat_soil_layers_stag=2": "dksat_soil_layers_stag=2",
            "geom_mean.dksat_soil_layers_stag=3": "dksat_soil_layers_stag=3",
            "geom_mean.dksat_soil_layers_stag=4": "dksat_soil_layers_stag=4",
            "geom_mean.psisat_soil_layers_stag=1": "psisat_soil_layers_stag=1",
            "geom_mean.psisat_soil_layers_stag=2": "psisat_soil_layers_stag=2",
            "geom_mean.psisat_soil_layers_stag=3": "psisat_soil_layers_stag=3",
            "geom_mean.psisat_soil_layers_stag=4": "psisat_soil_layers_stag=4",
            "mean.cwpvt": "cwpvt",
            "mean.mfsno": "mfsno",
            "mean.mp": "mp",
            "mean.refkdt": "refkdt",
            "mean.slope_1km": "slope", #NJF TODO check mean_slope vs slope
            "mean.smcmax_soil_layers_stag=1": "smcmax_soil_layers_stag=1",
            "mean.smcmax_soil_layers_stag=2": "smcmax_soil_layers_stag=2",
            "mean.smcmax_soil_layers_stag=3": "smcmax_soil_layers_stag=3",
            "mean.smcmax_soil_layers_stag=4": "smcmax_soil_layers_stag=4",
            "mean.smcwlt_soil_layers_stag=1": "smcwlt_soil_layers_stag=1",
            "mean.smcwlt_soil_layers_stag=2": "smcwlt_soil_layers_stag=2",
            "mean.smcwlt_soil_layers_stag=3": "smcwlt_soil_layers_stag=3",
            "mean.smcwlt_soil_layers_stag=4": "smcwlt_soil_layers_stag=4",
            "mean.vcmx25": "vcmx25",
            "mean.Coeff": "gw_Coeff",
            "mean.Zmax": "gw_Zmax",
            "mode.Expon": "gw_Expon",
            "centroid_x": "X",
            "centroid_y": "Y",
            "mean.impervious": "impervious_mean",
            "mean.elevation": "elevation_mean",
            "mean.slope": "slope_mean",
            "circ_mean.aspect": "aspect_c_mean",
            "dist_4.twi": "twi_dist_4",
        }
    )
    """Conus Mappings"""

    hi = MappingProxyType(
        {
            "divide_id": "divide_id",
            "mode.bexp_soil_layers_stag=1": "bexp_soil_layers_stag=1",
            "mode.bexp_soil_layers_stag=2": "bexp_soil_layers_stag=2",
            "mode.bexp_soil_layers_stag=3": "bexp_soil_layers_stag=3",
            "mode.bexp_soil_layers_stag=4": "bexp_soil_layers_stag=4",
            "mode.ISLTYP": "ISLTYP",
            "mode.IVGTYP": "IVGTYP",
            "geom_mean.dksat_soil_layers_stag=1": "dksat_soil_layers_stag=1",
            "geom_mean.dksat_soil_layers_stag=2": "dksat_soil_layers_stag=2",
            "geom_mean.dksat_soil_layers_stag=3": "dksat_soil_layers_stag=3",
            "geom_mean.dksat_soil_layers_stag=4": "dksat_soil_layers_stag=4",
            "geom_mean.psisat_soil_layers_stag=1": "psisat_soil_layers_stag=1",
            "geom_mean.psisat_soil_layers_stag=2": "psisat_soil_layers_stag=2",
            "geom_mean.psisat_soil_layers_stag=3": "psisat_soil_layers_stag=3",
            "geom_mean.psisat_soil_layers_stag=4": "psisat_soil_layers_stag=4",
            "mean.cwpvt": "cwpvt",
            "mean.mfsno": "mfsno",
            "mean.mp": "mp",
            "mean.refkdt": "refkdt",
            "mean.slope_1km": "slope_1km",
            "mean.smcmax_soil_layers_stag=1": "smcmax_soil_layers_stag=1",
            "mean.smcmax_soil_layers_stag=2": "smcmax_soil_layers_stag=2",
            "mean.smcmax_soil_layers_stag=3": "smcmax_soil_layers_stag=3",
            "mean.smcmax_soil_layers_stag=4": "smcmax_soil_layers_stag=4",
            "mean.smcwlt_soil_layers_stag=1": "smcwlt_soil_layers_stag=1",
            "mean.smcwlt_soil_layers_stag=2": "smcwlt_soil_layers_stag=2",
            "mean.smcwlt_soil_layers_stag=3": "smcwlt_soil_layers_stag=3",
            "mean.smcwlt_soil_layers_stag=4": "smcwlt_soil_layers_stag=4",
            "mean.vcmx25": "vcmx25",
            "mean.Coeff": "Coeff",
            "mean.Zmax": "Zmax",
            "mode.Expon": "Expon",
            "X": "X",
            "Y": "Y",
            "mean.impervious": "impervious",
            "mean.elevation": "elevation_mean",
            "mean.slope": "slope_mean",
            "circ_mean.aspect": "aspect_mean",
            "dist_4.twi": "twi_dist_4",
        }
    )
    """Hawaii Mappings"""

    ak = MappingProxyType(
        {
            "divide_id": "divide_id",
            "mode.bexp_soil_layers_stag=1": "bexp_soil_layers_stag=1",
            "mode.bexp_soil_layers_stag=2": "bexp_soil_layers_stag=2",
            "mode.bexp_soil_layers_stag=3": "bexp_soil_layers_stag=3",
            "mode.bexp_soil_layers_stag=4": "bexp_soil_layers_stag=4",
            "mode.ISLTYP": "ISLTYP",
            "mode.IVGTYP": "IVGTYP",
            "geom_mean.dksat_soil_layers_stag=1": "dksat_soil_layers_stag=1",
            "geom_mean.dksat_soil_layers_stag=2": "dksat_soil_layers_stag=2",
            "geom_mean.dksat_soil_layers_stag=3": "dksat_soil_layers_stag=3",
            "geom_mean.dksat_soil_layers_stag=4": "dksat_soil_layers_stag=4",
            "geom_mean.psisat_soil_layers_stag=1": "psisat_soil_layers_stag=1",
            "geom_mean.psisat_soil_layers_stag=2": "psisat_soil_layers_stag=2",
            "geom_mean.psisat_soil_layers_stag=3": "psisat_soil_layers_stag=3",
            "geom_mean.psisat_soil_layers_stag=4": "psisat_soil_layers_stag=4",
            "mean.cwpvt": "cwpvt",
            "mean.mfsno": "mfsno",
            "mean.mp": "mp",
            "mean.refkdt": "refkdt",
            "mean.slope_1km": "slope_1km",
            "mean.smcmax_soil_layers_stag=1": "smcmax_soil_layers_stag=1",
            "mean.smcmax_soil_layers_stag=2": "smcmax_soil_layers_stag=2",
            "mean.smcmax_soil_layers_stag=3": "smcmax_soil_layers_stag=3",
            "mean.smcmax_soil_layers_stag=4": "smcmax_soil_layers_stag=4",
            "mean.smcwlt_soil_layers_stag=1": "smcwlt_soil_layers_stag=1",
            "mean.smcwlt_soil_layers_stag=2": "smcwlt_soil_layers_stag=2",
            "mean.smcwlt_soil_layers_stag=3": "smcwlt_soil_layers_stag=3",
            "mean.smcwlt_soil_layers_stag=4": "smcwlt_soil_layers_stag=4",
            "mean.vcmx25": "vcmx25",
            "mean.Coeff": "Coeff",
            "mean.Zmax": "Zmax",
            "mode.Expon": "Expon",
            "X": "X",
            "Y": "Y",
            "mean.impervious": "impervious",
            "mean.elevation": "elevation",
            "mean.slope": "slope",
            "circ_mean.aspect": "aspect",
            "dist_4.twi": "twi",
        }
    )
    """Alaska Mappings"""

    pr = MappingProxyType(
        {
            "divide_id": "divide_id",
            "mode.bexp_Time=_soil_layers_stag=1": "bexp_soil_layers_stag=1",
            "mode.bexp_Time=_soil_layers_stag=2": "bexp_soil_layers_stag=2",
            "mode.bexp_Time=_soil_layers_stag=3": "bexp_soil_layers_stag=3",
            "mode.bexp_Time=_soil_layers_stag=4": "bexp_soil_layers_stag=4",
            "mode.ISLTYP": "ISLTYP",
            "mode.IVGTYP": "IVGTYP",
            "dksat_Time=_soil_layers_stag=1": "dksat_soil_layers_stag=1",
            "dksat_Time=_soil_layers_stag=2": "dksat_soil_layers_stag=2",
            "dksat_Time=_soil_layers_stag=3": "dksat_soil_layers_stag=3",
            "dksat_Time=_soil_layers_stag=4": "dksat_soil_layers_stag=4",
            "psisat_Time=_soil_layers_stag=1": "psisat_soil_layers_stag=1",
            "psisat_Time=_soil_layers_stag=2": "psisat_soil_layers_stag=2",
            "psisat_Time=_soil_layers_stag=3": "psisat_soil_layers_stag=3",
            "psisat_Time=_soil_layers_stag=4": "psisat_soil_layers_stag=4",
            "mean.cwpvt_Time=": "cwpvt",
            "mean.mfsno_Time=": "mfsno",
            "mean.mp_Time=": "mp",
            "mean.refkdt_Time=": "refkdt",
            "mean.slope_Time=": "slope_1km",
            "mean.smcmax_Time=_soil_layers_stag=1": "smcmax_soil_layers_stag=1",
            "mean.smcmax_Time=_soil_layers_stag=2": "smcmax_soil_layers_stag=2",
            "mean.smcmax_Time=_soil_layers_stag=3": "smcmax_soil_layers_stag=3",
            "mean.smcmax_Time=_soil_layers_stag=4": "smcmax_soil_layers_stag=4",
            "mean.smcwlt_Time=_soil_layers_stag=1": "smcwlt_soil_layers_stag=1",
            "mean.smcwlt_Time=_soil_layers_stag=2": "smcwlt_soil_layers_stag=2",
            "mean.smcwlt_Time=_soil_layers_stag=3": "smcwlt_soil_layers_stag=3",
            "mean.smcwlt_Time=_soil_layers_stag=4": "smcwlt_soil_layers_stag=4",
            "mean.vcmx25_Time=": "vcmx25",
            "mean.Coeff": "Coeff",
            "mean.Zmax": "Zmax",
            "mode.Expon": "Expon",
            "X": "X",
            "Y": "Y",
            "mean.impervious": "impervious",
            "mean.elevation": "elevation",
            "mean.slope": "slope",
            "circ_mean.aspect": "aspect",
            "dist_4.twi": "twi",
        }
    )
    """Puerto Rico Mappings"""

    vi = pr
    """U.S. Virgin Islands Mappings"""

    @classmethod
    def items(cls) -> typing.Iterator[tuple[str, typing.Mapping[str, str]]]:
        """
        Iterator of (domain name: str, mapping: typing.Mapping[str, str]) pairs
        defined in namespace.
        """
        yield from typing.cast(
            typing.Iterator[tuple[str, typing.Mapping[str, str]]], pub_cls_vars(cls)
        )
