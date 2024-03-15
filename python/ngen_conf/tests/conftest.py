import pytest
from pathlib import Path
from ngen.config.configurations import Forcing, Time, Routing
from ngen.config.formulation import Formulation
from ngen.config.cfe import CFE
from ngen.config.sloth import SLOTH
from ngen.config.noahowp import NoahOWP
from ngen.config.lgar import LGAR
from ngen.config.soil_freeze_thaw import SoilFreezeThaw
from ngen.config.soil_moisture_profile import SoilMoistureProfile
from ngen.config.topmod import Topmod
from ngen.config.lstm import LSTM
from ngen.config.multi import MultiBMI

# set the workdir relative to this test config
# and use that to look for test data
_workdir=Path(__file__).parent
_datadir = _workdir / "data"
_cfe_config_data_path = _datadir / "init_config_data" / "cat_87_bmi_config_cfe.ini"
_pet_config_data_path = _datadir / "init_config_data" / "pet.ini"
_noah_owp_config_data_path = _datadir / "init_config_data" / "noah_owp.namelist"

"""
Fixtures for setting up various ngen-conf components for testing
"""
@pytest.fixture
def forcing(request):
    which = request.param
    if which == "netcdf":
        provider = Forcing.Provider.NetCDF
    else:
        #default to csv
        provider = Forcing.Provider.CSV
    print(provider)
    forcing = _workdir.joinpath("data/forcing/")
    #Share forcing for all formulations
    return Forcing(file_pattern=".*{{id}}.*.csv", path=forcing, provider=provider)

@pytest.fixture
def time():
    return Time(start_time="2019-06-01 00:00:00", end_time="2019-06-07 23:00:00")

@pytest.fixture
def routing():
    return Routing(path="extern/t-route/src/ngen_routing/src", config="ngen_routing.yaml" )

@pytest.fixture
def cfe_params():
    path = _workdir.joinpath("data/CFE/")
    data = {
            'model_type_name': 'CFE',
            'name': 'bmi_c',
            'config_prefix':path,
            # 'config': "{{id}}_config.txt", 
            'config': "config.txt", 
            'library_prefix':path,
            'library': 'libfakecfe.so',
            'model_params':{'slope':0.42, 'expon':42}}
    return data

@pytest.fixture
def sloth_params():
    path = _workdir.joinpath("data/sloth/")
    data = {
            'model_type_name': 'SLOTH',
            'name': 'bmi_c++',
            'config_prefix':path,
            # 'config': "{{id}}_config.txt", 
            'config': "config.txt", 
            'library_prefix':path,
            'library': 'libfakesloth.so',
            'main_output_variable': 'TEST'}
    return data

@pytest.fixture
def topmod_params():
    path = _workdir.joinpath("data/CFE/")
    data = {
            'model_type_name': 'TOPMODEL',
            'name': 'bmi_c',
            'config_prefix':path,
            # 'config': "{{id}}_config.txt", 
            'config': "config.txt", 
            'library_prefix':path,
            'library': 'libfakecfe.so',
            'model_params':{'t0':0.42, 'szm':42}}
    return data

@pytest.fixture
def noahowp_params():
    path = _workdir.joinpath("data/NOAH/")
    libpath = _workdir.joinpath("data/CFE")
    data = {
            'model_type_name': 'NoahOWP',
            'name': 'bmi_fortran',
            'config_prefix':path,
            'config': "{{id}}.input", 
            'library_prefix': libpath,
            'library': 'libfakecfe.so'
            }
    return data   

@pytest.fixture
def lstm_params():
    path = _workdir.joinpath("data/CFE/")
    data = {
            'model_type_name': 'LSTM',
            'name': 'bmi_python',
            'config_prefix':path,
            'config': "{{id}}_config.txt"}
    return data

@pytest.fixture
def lgar_params():
    path = _workdir.joinpath("data/dne/")
    data = {
            'model_type_name': 'LGAR',
            'name': 'bmi_c++',
            'registration_function': 'none',
            'library': 'libfakecfe.so',
            'config_prefix': path,
            'config': "{{id}}_config.txt",
            }
    return data

@pytest.fixture
def soil_freeze_thaw_params():
    path = _workdir.joinpath("data/dne/")
    data = {
            'model_type_name': 'SoilFreezeThaw',
            'name': 'bmi_c++',
            'registration_function': 'none',
            'library': 'libfakecfe.so',
            'config_prefix': path,
            'config': "{{id}}_config.txt",
            }
    return data

@pytest.fixture
def soil_moisture_profile_params():
    path = _workdir.joinpath("data/dne/")
    data = {
            'model_type_name': 'SoilMoistureProfile',
            'name': 'bmi_c++',
            'registration_function': 'none',
            'library': 'libfakecfe.so',
            'config_prefix': path,
            'config': "{{id}}_config.txt",
            }
    return data

@pytest.fixture
def cfe(cfe_params):
    return CFE(**cfe_params)

@pytest.fixture
def sloth(sloth_params):
    return SLOTH(**sloth_params)

@pytest.fixture
def topmod(topmod_params):
    return Topmod(**topmod_params)

@pytest.fixture
def noahowp(noahowp_params):
    return NoahOWP(**noahowp_params)

@pytest.fixture
def lstm(lstm_params):
    return LSTM(**lstm_params)

@pytest.fixture
def lgar(lgar_params):
    return LGAR(**lgar_params)

@pytest.fixture
def soil_freeze_thaw(soil_freeze_thaw_params):
    return SoilFreezeThaw(**soil_freeze_thaw_params)

@pytest.fixture
def soil_moisture_profile(soil_moisture_profile_params):
    return SoilMoistureProfile(**soil_moisture_profile_params)

@pytest.fixture
def multi(cfe, noahowp):
    cfe.allow_exceed_end_time=True
    noahowp.allow_exceed_end_time=True
    f1 = Formulation(name=noahowp.name, params=noahowp)
    f2 = Formulation(name=cfe.name, params=cfe)
    return MultiBMI(modules=[f1, f2], allow_exceed_end_time=True)


@pytest.fixture
def multi_params(cfe, noahowp):
    data = {
        "name": "bmi_multi",
        "modules":[Formulation(name=noahowp.name, params=noahowp).dict(by_alias=True),
                       Formulation(name=cfe.name, params=cfe).dict(by_alias=True)]
            }
    return data

@pytest.fixture
def cfe_init_config() -> str:
    # drop eol char
    return _cfe_config_data_path.read_text().rstrip()

@pytest.fixture
def pet_init_config() -> str:
    # drop eol char
    return _pet_config_data_path.read_text().rstrip()

@pytest.fixture
def noah_owp_init_config() -> str:
    # drop eol char
    return _noah_owp_config_data_path.read_text().rstrip()
