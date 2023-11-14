from ngen.config.configurations import Routing


def test_initialize_routing_with_non_existant_path():
    o = Routing(t_route_config_file_with_path="some-fake-path.csv")
    assert not o.config.exists()
