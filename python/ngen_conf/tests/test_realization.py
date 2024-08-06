import pytest
from pathlib import Path
from ngen.config.realization import Realization, NgenRealization
from ngen.config.formulation import Formulation


@pytest.mark.parametrize("forcing",["csv", "netcdf"], indirect=True )
def test_realization(forcing, time, cfe):
    f = Formulation(name=cfe.name, params=cfe)
    r = Realization(forcing=forcing, formulations=[f])

@pytest.mark.parametrize("forcing",["csv", "netcdf"], indirect=True )
def test_ngen_global_realization(forcing, time, cfe):
    f = Formulation(name=cfe.name, params=cfe)
    r = Realization(formulations=[f], forcing=forcing)
    g = NgenRealization(global_config=r, time=time)
    # This can essentially be used at this point for an ngen integration test
    # by writing the realization and then running `ngen` with it...
    # with open("test_realization.json", 'w') as fp:
    #     fp.write( g.json(by_alias=True, exclude_none=True, indent=4))

@pytest.mark.parametrize("forcing",["csv", "netcdf"], indirect=True )
def test_ngen_global_multi_realization(forcing, time, multi):
    f = Formulation(name=multi.name, params=multi)
    r = Realization(formulations=[f], forcing=forcing)
    g = NgenRealization(global_config=r, time=time)
    # This can essentially be used at this point for an ngen integration test
    # by writing the realization and then running `ngen` with it...
    # with open("test_realization_multi.json", 'w') as fp:
    #     fp.write( g.json(by_alias=True, exclude_none=True, indent=4))

@pytest.mark.parametrize("forcing",["csv", "netcdf"], indirect=True )
def test_ngen_global_realization_with_output_root(forcing, time, cfe):
    f = Formulation(name=cfe.name, params=cfe)
    r = Realization(formulations=[f], forcing=forcing)
    g = NgenRealization(global_config=r, time=time, output_root=Path("/some/fake/path"))
