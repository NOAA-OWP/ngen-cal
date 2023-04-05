from ngen.init_config import utils
from ngen.config.init_config.cfe import CFE


def test_cfe(cfe_init_config: str):
    assert utils.merge_class_attr(CFE, "Config.space_around_delimiters") is False
    assert utils.merge_class_attr(CFE, "Config.no_section_headers") is True
    o = CFE.from_ini_str(cfe_init_config)
    assert o.to_ini_str() == cfe_init_config
