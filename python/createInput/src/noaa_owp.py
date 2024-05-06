"""
This module is taken from ngen_config_gen open source package.
Author made further modifications. 
"""

from typing import Any, Dict, List, TYPE_CHECKING
from collections import defaultdict
from pathlib import Path

from pydantic import BaseModel

if TYPE_CHECKING:
    from ngen.config_gen.hook_providers import HookProvider

import math

from ngen.config.init_config.noahowp import (
    NoahOWP as NoahOWPConfig,
    ModelOptions,
    Location,
    Forcing,
    Structure,
    InitialValues,
    LandSurfaceType,
)
from ngen.config.init_config.noahowp_options import (
    DynamicVegOption,
    CanopyStomResistOption,
    SoilTempBoundaryOption,
    RunoffOption,
    SfcDragCoeffOption,
    FrozenSoilOption,
    SupercooledWaterOption,
    RadiativeTransferOption,
    SnowAlbedoOption,
    PrecipPhaseOption,
    SnowsoilTempTimeOption,
    SubsurfaceOption,
    StomatalResistanceOption,
    EvapSrfcResistanceOption,
    DrainageOption,
    DynamicVicOption,
    CropModelOption,
)


class NoahOWP:
    """
    NWM 2.2.3 analysis assim physics options
    source: https://www.nco.ncep.noaa.gov/pmb/codes/nwprod/nwm.v2.2.3/parm/analysis_assim/namelist.hrldas
    ! Physics options (see the documentation for details)
    | NoahOWP Name                | NoahMP Name                         | NWM 2.2.3 analysis assim physics options |
    |-----------------------------|-------------------------------------|------------------------------------------|
    | dynamic_veg_option          | DYNAMIC_VEG_OPTION                  | 4                                        |
    | canopy_stom_resist_option   | CANOPY_STOMATAL_RESISTANCE_OPTION   | 1                                        |
    | stomatal_resistance_option  | BTR_OPTION                          | 1                                        |
    | runoff_option               | RUNOFF_OPTION                       | 3                                        |
    | sfc_drag_coeff_option       | SURFACE_DRAG_OPTION                 | 1                                        |
    | frozen_soil_option          | FROZEN_SOIL_OPTION                  | 1                                        |
    | supercooled_water_option    | SUPERCOOLED_WATER_OPTION            | 1                                        |
    | radiative_transfer_option   | RADIATIVE_TRANSFER_OPTION           | 3                                        |
    | snow_albedo_option          | SNOW_ALBEDO_OPTION                  | 1                                        |
    | precip_phase_option         | PCP_PARTITION_OPTION                | 1                                        |
    | soil_temp_boundary_option   | TBOT_OPTION                         | 2                                        |
    | snowsoil_temp_time_option   | TEMP_TIME_SCHEME_OPTION             | 3                                        |
    | no glacier option           | GLACIER_OPTION                      | 2                                        |
    | evap_srfc_resistance_option | SURFACE_RESISTANCE_OPTION           | 4                                        |

    NWM 3.0.6 analysis assim physics options
    source: https://www.nco.ncep.noaa.gov/pmb/codes/nwprod/nwm.v3.0.6/parm/analysis_assim/namelist.hrldas
    ! Physics options (see the documentation for details)
    | NoahOWP Name                | NoahMP Name                         | NWM 3.0.6 analysis assim physics options |
    |-----------------------------|-------------------------------------|------------------------------------------|
    | dynamic_veg_option          | DYNAMIC_VEG_OPTION                  | 4                                        |
    | canopy_stom_resist_option   | CANOPY_STOMATAL_RESISTANCE_OPTION   | 1                                        |
    | stomatal_resistance_option  | BTR_OPTION                          | 1                                        |
    | runoff_option               | RUNOFF_OPTION                       | 7                                        |
    | sfc_drag_coeff_option       | SURFACE_DRAG_OPTION                 | 1                                        |
    | frozen_soil_option          | FROZEN_SOIL_OPTION                  | 1                                        |
    | supercooled_water_option    | SUPERCOOLED_WATER_OPTION            | 1                                        |
    | radiative_transfer_option   | RADIATIVE_TRANSFER_OPTION           | 3                                        |
    | snow_albedo_option          | SNOW_ALBEDO_OPTION                  | 1                                        |
    | precip_phase_option         | PCP_PARTITION_OPTION                | 1                                        |
    | soil_temp_boundary_option   | TBOT_OPTION                         | 2                                        |
    | snowsoil_temp_time_option   | TEMP_TIME_SCHEME_OPTION             | 3                                        |
    | no glacier option           | GLACIER_OPTION                      | 2                                        |
    | evap_srfc_resistance_option | SURFACE_RESISTANCE_OPTION           | 4                                        |
    |                             | IMPERV_OPTION                       | 2 (0: none; 1: total; 2: Alley&Veenhuis; |
    |                             |                                     |    9: orig)                              |

    """

    def __init__(self, start_time: str, end_time: str, parameter_dir: Path):
        self.data = defaultdict(dict)
        # NOTE: this might be handled differently in the future
        self.data["parameters"]["parameter_dir"] = parameter_dir

        # NOTE: expects "%Y%m%d%H%M" (e.g. 200012311730)
        self.data["timing"]["startdate"] = start_time
        self.data["timing"]["enddate"] = end_time

        # NOTE: these parameters will likely be removed in the future. They are not used if noah owp
        # is compiled for use with NextGen.
        self.data["timing"]["forcing_filename"] = Path("")
        self.data["timing"]["output_filename"] = Path("")

    def _v2_defaults(self) -> None:
        # ---------------------------------- Timing ---------------------------------- #
        # NOTE: in the future this _should_ be pulled from a forcing metadata hook (if one ever exists)
        self.data["timing"]["dt"] = 3600

        # -------------------------------- Parameters -------------------------------- #
        # NOTE: Wrf-Hydro configured as NWM uses USGS vegitation classes. Thus, so does HF v1.2 and v2.0
        self.data["parameters"]["veg_class_name"] = "USGS"

        # TODO: determine how to handle `parameter_dir`
        # NOTE: theses _could_ be bundled as package data
        # NOTE: could a parameter to the initializer
        # NOTE: moved to __init__ for now
        # self.data["parameters"]["parameter_dir"] =

        # looking through the from wrf-hydro source, it appears that wrf-hydro hard codes `STAS` as the `soil_class_name`
        # see https://sourcegraph.com/search?q=context:global+repo:https://github.com/NCAR/wrf_hydro_nwm_public+STAS&patternType=standard&sm=1&groupBy=repo
        self.data["parameters"]["soil_class_name"] = "STAS"  # | "STAS-RUC"

        # ---------------------------------- Forcing --------------------------------- #
        # measurement height for wind speed [m]
        # NOTE: in the future this _should_ be pulled from a forcing metadata hook (if one ever exists)
        zref = 10.0
        # rain-snow temperature threshold
        rain_snow_thresh = 0.5
        self.data["forcing"] = Forcing(zref=zref, rain_snow_thresh=rain_snow_thresh)

        # ------------------------------- Model Options ------------------------------ #
        dynamic_veg_option: DynamicVegOption = (
            DynamicVegOption.off_use_lai_table_use_max_vegetation_fraction
        )
        canopy_stom_resist_option = CanopyStomResistOption.ball_berry
        stomatal_resistance_option = StomatalResistanceOption.noah
        runoff_option = RunoffOption.original_surface_and_subsurface_runoff
        sfc_drag_coeff_option = SfcDragCoeffOption.m_o
        frozen_soil_option = FrozenSoilOption.linear_effects
        supercooled_water_option = SupercooledWaterOption.no_iteration
        radiative_transfer_option = (
            RadiativeTransferOption.two_stream_applied_to_vegetated_fraction
        )
        snow_albedo_option = SnowAlbedoOption.BATS
        precip_phase_option = PrecipPhaseOption.user_defined_wet_bulb_temperature_threshold
        soil_temp_boundary_option = SoilTempBoundaryOption.tbot_at_zbot
        # TODO: needs further verification
        snowsoil_temp_time_option = (
            SnowsoilTempTimeOption.semo_implicit_with_fsno_for_ts
        )
        # no glacier option
        evap_srfc_resistance_option = (
            EvapSrfcResistanceOption.sakaguchi_and_zeng_for_nonsnow_rsurf_eq_rsurf_snow_for_snow
        )
        # non noahmp options
        drainage_option = DrainageOption.dynamic_vic_runoff_with_dynamic_vic_runoff
        dynamic_vic_option = DynamicVicOption.philip
        crop_model_option = CropModelOption.none
        subsurface_option = SubsurfaceOption.one_way_coupled_hydrostatic

        model_options = ModelOptions(
            precip_phase_option=precip_phase_option,
            snow_albedo_option=snow_albedo_option,
            dynamic_veg_option=dynamic_veg_option,
            runoff_option=runoff_option,
            drainage_option=drainage_option,
            frozen_soil_option=frozen_soil_option,
            dynamic_vic_option=dynamic_vic_option,
            radiative_transfer_option=radiative_transfer_option,
            sfc_drag_coeff_option=sfc_drag_coeff_option,
            canopy_stom_resist_option=canopy_stom_resist_option,
            crop_model_option=crop_model_option,
            snowsoil_temp_time_option=snowsoil_temp_time_option,
            soil_temp_boundary_option=soil_temp_boundary_option,
            supercooled_water_option=supercooled_water_option,
            stomatal_resistance_option=stomatal_resistance_option,
            evap_srfc_resistance_option=evap_srfc_resistance_option,
            subsurface_option=subsurface_option,
        )
        self.data["model_options"] = model_options

        # ------------------------------- InitialValues ------------------------------ #

        # snow/soil level thickness [m]
        # all nwm version (including 3.0) have always used soil horizons of 10cm 30cm 60cm and 1m; see last 4 values of dzsnso
        # NOTE: len nsnow + nsoil; thus [nsnow..., nsoil...] in this order
        # https://github.com/NOAA-OWP/noah-owp-modular/blob/30d0f53e8c14acc4ce74018e06ff7c9410ecc13c/src/DomainType.f90#L66
        # if you are looking at the fortran source, this is indexed like:
        # where [-2:0] are snow and [1:4] are soil
        #                     [ -2,  -1,   0,   1    2,   3,   4]
        dzsnso: List[float] = [0.0, 0.0, 0.0, 0.1, 0.3, 0.6, 1.0]

        # initial soil ice profile [m^3/m^3]
        # NOTE: len nsoil
        # https://github.com/NOAA-OWP/noah-owp-modular/blob/30d0f53e8c14acc4ce74018e06ff7c9410ecc13c/src/WaterType.f90#L110
        # NOTE: These values likely make no sense
        sice: List[float] = [0.0, 0.0, 0.0, 0.0]

        # initial soil liquid profile [m^3/m^3]
        # NOTE: len nsoil
        # https://github.com/NOAA-OWP/noah-owp-modular/blob/30d0f53e8c14acc4ce74018e06ff7c9410ecc13c/src/WaterType.f90#L111
        sh2o: List[float] = [0.3, 0.3, 0.3, 0.3]

        # initial water table depth below surface [m]
        # NOTE: not sure if this _should_ ever be derived. my intuition is this is -2 b.c. the total
        # soil horizon height is 2m (see `dzsnoso`)
        zwt: float = -2.0

        initial_values = InitialValues(
            dzsnso=dzsnso,
            sice=sice,
            sh2o=sh2o,
            zwt=zwt,
        )
        self.data["initial_values"] = initial_values

    def hydrofabric_linked_data_hook(
        self, version: str, divide_id: str, data: Dict[str, Any]
    ) -> None:
        # --------------------------------- Location --------------------------------- #
        lon = data["X"]
        lat = data["Y"]
        terrain_slope = data['slope_mean']
        azimuth = data["aspect_c_mean"]
        self.data["location"] = Location(
            lon=lon, lat=lat, terrain_slope=terrain_slope, azimuth=azimuth
        )

        # --------------------------------- Structure -------------------------------- #
        # NOTE: Wrf-Hydro configured as NWM uses STAS soil classes. Thus, so does HF v1.2 and v2.0
        isltyp = data["ISLTYP"]
        # all nwm versions (including 3.0) have used 4 soil horizons
        nsoil = 4
        nsnow = 3
        # NOTE: Wrf-Hydro configured as NWM uses USGS vegetation classes. Thus, so does HF v1.2 and v2.0
        # NOTE: this can be derived from Parameters `veg_class_name` field (USGS=27; MODIS=20)
        nveg = 27
        vegtyp = data["IVGTYP"]
        # crop type (SET TO 0, no crops currently supported)
        # source: https://github.com/NOAA-OWP/noah-owp-modular/blob/30d0f53e8c14acc4ce74018e06ff7c9410ecc13c/src/NamelistRead.f90#L36
        croptype = 0

        # NOTE: 16 = water bodies in USGS vegetation classification (see MPTABLE.TBL)
        USGS_VEG_IS_WATER = 16
        if vegtyp == USGS_VEG_IS_WATER:
            sfctyp = LandSurfaceType.lake
        else:
            sfctyp = LandSurfaceType.soil

        # TODO: not sure where this comes from
        # soil color index for soil albedo
        # https://github.com/NOAA-OWP/noah-owp-modular/blob/30d0f53e8c14acc4ce74018e06ff7c9410ecc13c/docs/changelog.md?plain=1#L35C7-L35C168
        # > SOILCOLOR is hard-coded as 4 in module_sf_noahmpdrv.F in the current release of HRLDAS. SOILCOLOR is used to select the albedo values for dry and saturated soil.
        # NOTE: it appears that the soil color indexes into the ALBSAT_VIS, ALBSAT_NIR, ALBDRY_VIS, ALBDRY_NIR tables
        # https://github.com/NOAA-OWP/noah-owp-modular/blob/30d0f53e8c14acc4ce74018e06ff7c9410ecc13c/parameters/MPTABLE.TBL#L328-L331
        # here is the indexing
        # https://github.com/NOAA-OWP/noah-owp-modular/blob/30d0f53e8c14acc4ce74018e06ff7c9410ecc13c/src/ParametersType.f90#L303-L306
        # NOTE: looks like for HRLDAS this is 4
        soilcolor: int = 4
        structure = Structure(
            isltyp=isltyp,
            nsoil=nsoil,
            nsnow=nsnow,
            nveg=nveg,
            vegtyp=vegtyp,
            # crop type (SET TO 0, no crops currently supported)
            # source: https://github.com/NOAA-OWP/noah-owp-modular/blob/30d0f53e8c14acc4ce74018e06ff7c9410ecc13c/src/NamelistRead.f90#L36
            croptype=croptype,
            sfctyp=sfctyp,
            soilcolor=soilcolor,
        )
        self.data["structure"] = structure

    def visit(self, hook_provider: "HookProvider") -> None:
        hook_provider.provide_hydrofabric_linked_data(self)

        self._v2_defaults()

    def build(self) -> BaseModel:
        return NoahOWPConfig(**self.data)
