from ngen.config.bmi_formulation import BMIParams, LinkItem


def test_valid_bmi_params_model_params_type_variants():
    model_params = {
        "natural_key": 42,
        "real_key": 42.0,
        "natural_seq": [1, 1, 2, 3, 5],
        "real_seq": [1.0, 10.0, 100.0],
        "link_item": {"source": "somewhere", "from": "something"},
        "link_item_no_from": {"source": "somewhere"},
    }

    bmi_params = BMIParams(
        name="test",
        model_type_name="test_model",
        main_output_variable="nothing",
        config="fake_{{id}}.toml",
        model_params=model_params,
    )

    model_params_serialized_form = {
        "natural_key": 42,
        "real_key": 42.0,
        "natural_seq": [1, 1, 2, 3, 5],
        "real_seq": [1.0, 10.0, 100.0],
        "link_item": LinkItem(**{"source": "somewhere", "from": "something"}),
        "link_item_no_from": LinkItem(**{"source": "somewhere"}),
    }
    assert bmi_params.model_params == model_params_serialized_form
