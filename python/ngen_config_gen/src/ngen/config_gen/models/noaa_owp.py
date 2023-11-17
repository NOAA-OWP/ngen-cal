from typing import Any, Dict, List, TYPE_CHECKING
from collections import defaultdict

from pydantic import BaseModel

if TYPE_CHECKING:
    from ..hook_providers import HookProvider

import math

from ngen.config.init_config.noahowp import (
    NoahOWP as NoahOWPConfig,
    ModelOptions,
    Timing,
    Parameters,
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


class NoahOWPHooks:
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

    def __init__(self):
        self.data = defaultdict(dict)

    def _v2_defaults(self) -> None:
        # -------------------------------- Parameters -------------------------------- #
        # NOTE: Wrf-Hydro configured as NWM uses USGS vegitation classes. Thus, so does HF v1.2
        self.data["parameters"]["veg_class_name"] = "USGS"
        # TODO: determine how to handle `parameter_dir`
        # NOTE: theses _could_ be bundled as package data
        # self.data["parameters"]["parameter_dir"] =

        # looking through the from wrf-hydro source, it appears that wrf-hydro hard codes `STAS` as the `soil_class_name`
        # see https://sourcegraph.com/search?q=context:global+repo:https://github.com/NCAR/wrf_hydro_nwm_public+STAS&patternType=standard&sm=1&groupBy=repo
        self.data["parameters"]["soil_class_name"] = "STAS"  # | "STAS-RUC"

        # ---------------------------------- Forcing --------------------------------- #
        # measurement height for wind speed [m]
        zref = 10.0
        # TODO: not sure if this is a sane default
        # rain-snow temperature threshold
        rain_snow_thresh = 1.0
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
        precip_phase_option = PrecipPhaseOption.sntherm
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
        subsurface_option = SubsurfaceOption.noah_mp

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
        # TODO: not sure where to get these from
        # NOTE: These values likely make no sense
        dzsnso: List[float] = [0.0, 0.0, 0.0, 0.1, 0.3, 0.6, 1.0]
        sice: List[float] = [0.0, 0.0, 0.0, 0.0]
        sh2o: List[float] = [0.3, 0.3, 0.3, 0.3]
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
        # Location
        lon = data["X"]
        lat = data["Y"]

        # TODO: i think the units are wrong m / km need degrees
        # TODO: this needs to be checked
        METERS_IN_KM = 1_000
        slope_m_km = data["slope"]
        slope_m_m = slope_m_km / METERS_IN_KM
        slope_deg = math.degrees(math.tan(slope_m_m))
        terrain_slope = slope_deg
        # TODO: not sure if this is right and where to get this from
        azimuth = data["aspect_c_mean"]
        self.data["location"] = Location(
            lon=lon, lat=lat, terrain_slope=terrain_slope, azimuth=azimuth
        )

        # --------------------------------- Structure -------------------------------- #
        # NOTE: Wrf-Hydro configured as NWM uses STAS soil classes. Thus, so does HF v1.2
        isltyp = data["ISLTYP"]
        nsoil = 4
        nsnow = 3
        # NOTE: Wrf-Hydro configured as NWM uses USGS vegitation classes. Thus, so does HF v1.2
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

    def build(self) -> BaseModel:
        # NoahOWPConfig(**self.data)
        # NoahOWPConfig(
        #     timing=
        #     parameters=,
        #     location
        #     forcing
        #     model_options=
        #     structure=
        #     initial_values=
        # )
        pass
