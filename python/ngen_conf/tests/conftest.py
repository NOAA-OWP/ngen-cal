import pytest
from pathlib import Path
from ngen.config.configurations import Forcing, Time, Routing
from ngen.config.formulation import Formulation
from ngen.config.cfe import CFE
from ngen.config.sloth import SLOTH
from ngen.config.noahowp import NoahOWP
from ngen.config.multi import MultiBMI

#set the workdir relative to this test config
#and use that to look for test data
_workdir=Path(__file__).parent

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
    data = {'config_prefix':path, 
            # 'config': "{{id}}_config.txt", 
            'config': "config.txt", 
            'library_prefix':path,
            'library': 'libfakecfe.so',
            'model_params':{'slope':0.42, 'expon':42}}
    return data

@pytest.fixture
def sloth_params():
    path = _workdir.joinpath("data/sloth/")
    data = {'config_prefix':path, 
            # 'config': "{{id}}_config.txt", 
            'config': "config.txt", 
            'library_prefix':path,
            'library': 'libfakesloth.so',
            'main_output_variable': 'TEST'}
    return data

@pytest.fixture
def topmod_params():
    path = _workdir.joinpath("data/CFE/")
    data = {'config_prefix':path, 
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
    data = {'config_prefix':path, 
            'config': "{{id}}.input", 
            'library_prefix': libpath,
            'library': 'libfakecfe.so'
            }
    return data   

@pytest.fixture
def cfe(cfe_params):
    return CFE(**cfe_params)

@pytest.fixture
def sloth(sloth_params):
    return SLOTH(**sloth_params)

@pytest.fixture
def noahowp(noahowp_params):
    return NoahOWP(**noahowp_params)

@pytest.fixture
def multi(cfe, noahowp, forcing):
    cfe.allow_exceed_end_time=True
    noahowp.allow_exceed_end_time=True
    f1 = Formulation(name=noahowp.name, params=noahowp)
    f2 = Formulation(name=cfe.name, params=cfe)
    return MultiBMI(modules=[f1.dict(), f2.dict()], allow_exceed_end_time=True)

@pytest.fixture
def lstm_params():
    path = _workdir.joinpath("data/CFE/")
    data = {'config_prefix':path, 
            'config': "{{id}}_config.txt"}
    return data

@pytest.fixture
def multi_params(cfe, noahowp):
    data = {"modules":[Formulation(name=noahowp.name, params=noahowp).dict(), 
                       Formulation(name=cfe.name, params=cfe).dict()]
            }
    return data
