from ngen.config.configurations import Forcing


def test_initialize_forcing_with_non_existant_path():
    o = Forcing(path="some-fake-path.csv", provider=Forcing.Provider.CSV)
    assert not o.path.exists()
