from __future__ import annotations

from enum import Enum


class PrecipPhaseOption(int, Enum):
    """
    integer :: opt_snf    ! precip_phase_option: options for determining precipitation phase
        1 -> Jordan (1991) SNTHERM equation
        2 -> rain-snow air temperature threshold of 2.2°C
        3 -> rain-snow air temperature threshold of 0°C
        4 -> precipitation phase from weather model
        5 -> user-defined air temperature threshold
        6 -> user-defined wet bulb temperature threshold
        7 -> binary logistic regression model from Jennings et al. (2018)
    source: https://github.com/NOAA-OWP/noah-owp-modular/blob/30d0f53e8c14acc4ce74018e06ff7c9410ecc13c/src/OptionsType.f90#L11-L18
    """

    sntherm = 1
    rain_snow_air_temp_threshold_2_2_C = 2
    rain_snow_air_temp_threshold_0_C = 3
    precip_phase_from_weather_model = 4
    user_defined_air_temp_threshold = 5
    user_defined_wet_bulb_temperature_threshold = 6
    binary_logistic_regression_model = 7


class RunoffOption(int, Enum):
    """
    integer :: opt_run    ! runoff_option: options for runoff
        1 -> TOPMODEL with groundwater (Niu et al. 2007 JGR)
        2 -> TOPMODEL with an equilibrium water table (Niu et al. 2005 JGR)
        3 -> original surface and subsurface runoff (free drainage)
        4 -> BATS surface and subsurface runoff (free drainage)
        5 -> Miguez-Macho&Fan groundwater scheme (Miguez-Macho et al. 2007 JGR; Fan et al. 2007 JGR)
        6 -> VIC runoff
        7 -> Xinanjiang runoff
        8 -> Dynamic VIC runoff

    source: https://github.com/NOAA-OWP/noah-owp-modular/blob/30d0f53e8c14acc4ce74018e06ff7c9410ecc13c/src/OptionsType.f90#L19-L27
    """

    topmodel_with_groundwater = 1
    topmodel_with_equilibrium_water_table = 2
    original_surface_and_subsurface_runoff = 3
    bats_surface_and_subsurface_runoff = 4
    miguez_macho_fan_groundwater_scheme = 5
    vic_runoff = 6
    xinanjiang_runoff = 7
    dynamic_vic_runoff = 8


class DrainageOption(int, Enum):
    """
    integer :: opt_drn    ! drainage_option
                        ! options for drainage
        1 -> Subsurface runoff scheme from groundwater module (Niu et al. 2007 JGR)
        2 -> Subsurface runoff scheme with an equilibrium water table (Niu et al. 2005 JGR)
        3 -> original subsurface runoff (free drainage)
        4 -> original subsurface runoff (same as opt_drn = 3 but uses values from opt_run = 4)
        5 -> drainage with MMF shallow water table scheme
        6 -> VIC with free drainage (same as opt_drn = 3 but uses values from opt_run = 6)
        7 -> Xinanjiang runoff (same as opt_drn = 3 but uses values from opt_run = 7)
        8 -> Dynamic VIC runoff (same as opt_drn = 3 but uses values from opt_run = 8)
    source: https://github.com/NOAA-OWP/noah-owp-modular/blob/30d0f53e8c14acc4ce74018e06ff7c9410ecc13c/src/OptionsType.f90#L28-L37
    """

    subsurface_runoff_scheme_from_groundwater_module = 1
    subsurface_runoff_scheme_with_an_equilibrium_water_table = 2
    original_subsurface_runoff = 3
    original_subsurface_runoff_with_bats = 4
    drainage_with_mmf_shallow_water_table_scheme = 5
    vic_with_free_drainage_with_vic_runoff = 6
    xinanjiang_runoff_with_xinanjiang_runoff = 7
    dynamic_vic_runoff_with_dynamic_vic_runoff = 8


class FrozenSoilOption(int, Enum):
    """
    integer :: opt_inf    ! frozen_soil_option
                        ! options for frozen soil permeability
        1 -> linear effects, more permeable (Niu and Yang, 2006, JHM)
        2 -> nonlinear effects, less permeable (old)
    source: https://github.com/NOAA-OWP/noah-owp-modular/blob/30d0f53e8c14acc4ce74018e06ff7c9410ecc13c/src/OptionsType.f90#L38-L41
    """

    linear_effects = 1
    non_linear_effects = 2


class DynamicVicOption(int, Enum):
    """
    integer :: opt_infdv  ! dynamic_vic_option
                        ! options for infiltration in dynamic VIC runoff scheme
        1 -> Philip scheme,
        2 -> Green-Ampt scheme
        3 -> Smith-Parlange scheme
    source: https://github.com/NOAA-OWP/noah-owp-modular/blob/30d0f53e8c14acc4ce74018e06ff7c9410ecc13c/src/OptionsType.f90#L42-L46
    """

    philip = 1
    green_ampt = 2
    smith_parlange = 3


class DynamicVegOption(int, Enum):
    """
    integer :: dveg       ! dynamic_veg_option
                        ! options for dynamic vegetation scheme
        1 -> off (use table LAI; use FVEG = SHDFAC from input)
        2 -> on  (together with OPT_CRS = 1)
        3 -> off (use table LAI; calculate FVEG)
        4 -> off (use table LAI; use maximum vegetation fraction)
        5 -> on  (use maximum vegetation fraction)
        6 -> on  (use FVEG = SHDFAC from input)
        7 -> off (use input LAI; use FVEG = SHDFAC from input)
        8 -> off (use input LAI; calculate FVEG)
        9 -> off (use input LAI; use maximum vegetation fraction)
    source: https://github.com/NOAA-OWP/noah-owp-modular/blob/30d0f53e8c14acc4ce74018e06ff7c9410ecc13c/src/OptionsType.f90#L47-L57
    """

    off_use_lai_table_fveg_eq_shdfac_from_input = 1
    on_with_canopy_stom_resist_option_ball_berry = 2
    off_use_lai_table_calculate_fveg = 3
    off_use_lai_table_use_max_vegetation_fraction = 4
    on_use_max_vegetation_fraction = 5
    on_use_fveg_eq_shdfac_from_input = 6
    off_use_input_lai_use_fveg_eq_shdfac_from_input = 7
    off_use_input_lai_calculate_fveg = 8
    off_use_input_lai_use_max_vegetation_fraction = 9


class SnowAlbedoOption(int, Enum):
    """
    integer :: opt_alb    ! snow_albedo_option
                        ! options for snow albedo
        1 -> BATS
        2 -> CLASS
    source: https://github.com/NOAA-OWP/noah-owp-modular/blob/30d0f53e8c14acc4ce74018e06ff7c9410ecc13c/src/OptionsType.f90#L58-L61
    """

    BATS = 1
    CLASS = 2


class RadiativeTransferOption(int, Enum):
    """
    integer :: opt_rad    ! radiative_transfer_option
                        ! options for radiative transfer
        1 -> modified two-stream (gap = F(solar angle, 3D structure ...)<1-FVEG)
        2 -> two-stream applied to grid-cell (gap = 0)
        3 -> two-stream applied to vegetated fraction (gap=1-FVEG)
    source: https://github.com/NOAA-OWP/noah-owp-modular/blob/30d0f53e8c14acc4ce74018e06ff7c9410ecc13c/src/OptionsType.f90#L62-L66
    """

    modified_two_stream = 1
    two_stream_applied_to_grid_cell = 2
    two_stream_applied_to_vegetated_fraction = 3


class SfcDragCoeffOption(int, Enum):
    """
    integer :: opt_sfc    ! sfc_drag_coeff_option
                        ! options for surface layer drag coeff (CH & CM)
        1 -> M-O
        2 -> original Noah (Chen97)
    source: https://github.com/NOAA-OWP/noah-owp-modular/blob/30d0f53e8c14acc4ce74018e06ff7c9410ecc13c/src/OptionsType.f90#L67-L70
    """

    m_o = 1
    noah = 2


class CanopyStomResistOption(int, Enum):
    """
    integer :: opt_crs    ! canopy_stom_resist_option
                        ! options for canopy stomatal resistance
        1 -> Ball-Berry
        2 -> Jarvis
    source: https://github.com/NOAA-OWP/noah-owp-modular/blob/30d0f53e8c14acc4ce74018e06ff7c9410ecc13c/src/OptionsType.f90#L71-L74
    """

    ball_berry = 1
    jarvis = 2


class CropModelOption(int, Enum):
    """
    integer :: opt_crop   ! crop_model_option
                        ! options for crop model
                        ! NO CROP MODEL CURRENTLY SUPPORTED
        0 -> No crop model, will run default dynamic vegetation
    source: https://github.com/NOAA-OWP/noah-owp-modular/blob/30d0f53e8c14acc4ce74018e06ff7c9410ecc13c/src/OptionsType.f90#L75-L78
    """

    none = 0


class SnowsoilTempTimeOption(int, Enum):
    """
    integer :: opt_stc    ! snowsoil_temp_time_option
                        ! options for snow/soil temperature time scheme (only layer 1)
        1 -> semi-implicit; flux top boundary condition
        2 -> full implicit (original Noah); temperature top boundary condition
        3 -> same as 1, but FSNO for TS calculation (generally improves snow; v3.7)
    source: https://github.com/NOAA-OWP/noah-owp-modular/blob/30d0f53e8c14acc4ce74018e06ff7c9410ecc13c/src/OptionsType.f90#L79-L83
    """

    semi_implicit = 1
    full_implicit = 2
    semo_implicit_with_fsno_for_ts = 3


class SoilTempBoundaryOption(int, Enum):
    """
    integer :: opt_tbot   ! soil_temp_boundary_option
                        ! options for lower boundary condition of soil temperature
        1 -> zero heat flux from bottom (ZBOT and TBOT not used)
        2 -> TBOT at ZBOT (8m) read from a file (original Noah)
    source: https://github.com/NOAA-OWP/noah-owp-modular/blob/30d0f53e8c14acc4ce74018e06ff7c9410ecc13c/src/OptionsType.f90#L84-L87
    """

    zero_heat_flux_from_bottom = 1
    tbot_at_zbot = 2


class SupercooledWaterOption(int, Enum):
    """
    integer :: opt_frz    ! supercooled_water_option
                        ! options for supercooled liquid water (or ice fraction)
        1 -> no iteration (Niu and Yang, 2006 JHM)
        2 -> nonlinear effects, less permeable (old)
    source: https://github.com/NOAA-OWP/noah-owp-modular/blob/30d0f53e8c14acc4ce74018e06ff7c9410ecc13c/src/OptionsType.f90#L88-L91
    """

    no_iteration = 1
    nonlinear = 2


class StomatalResistanceOption(int, Enum):
    """
    integer :: opt_btr    ! stomatal_resistance_option
                        ! options for soil moisture factor for stomatal resistance
        1 -> Noah (soil moisture)
        2 -> CLM  (matric potential)
        3 -> SSiB (matric potential)
    source: https://github.com/NOAA-OWP/noah-owp-modular/blob/30d0f53e8c14acc4ce74018e06ff7c9410ecc13c/src/OptionsType.f90#L92-L96
    """

    noah = 1
    clm = 2
    ssib = 3


class EvapSrfcResistanceOption(int, Enum):
    """
    integer :: opt_rsf    ! evap_srfc_resistance_option
                        ! options for surface resistance to evaporation/sublimation
        1 -> Sakaguchi and Zeng, 2009
        2 -> Sellers (1992)
        3 -> adjusted Sellers to decrease RSURF for wet soil
        4 -> option 1 for non-snow; rsurf = rsurf_snow for snow (set in MPTABLE); AD v3.8
    source: https://github.com/NOAA-OWP/noah-owp-modular/blob/30d0f53e8c14acc4ce74018e06ff7c9410ecc13c/src/OptionsType.f90#L97-L102
    """

    sakaguchi_and_zeng = 1
    sellers = 2
    adjusted_sellers = 3
    sakaguchi_and_zeng_for_nonsnow_rsurf_eq_rsurf_snow_for_snow = 4


class SubsurfaceOption(int, Enum):
    """
    integer :: opt_sub    ! subsurface_option
                        ! options for subsurface realization
        1 -> full Noah-MP style subsurface
        2 -> one-way coupled hydrostatic
        3 -> two-way coupled (NOT IMPLEMENTED YET)
    source: https://github.com/NOAA-OWP/noah-owp-modular/blob/30d0f53e8c14acc4ce74018e06ff7c9410ecc13c/src/OptionsType.f90#L103-L107
    """

    noah_mp = 1
    one_way_coupled_hydrostatic = 2
    # two_way_coupled_hydrostatic = 3
