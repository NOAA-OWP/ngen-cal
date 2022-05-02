config = {
        "global": {
        "formulations": [
            {
                "name": "tshirt_c",
                "params": {
                    "maxsmc": 0.439,
                    "wltsmc": 0.066,
                    "satdk": 3.38e-06,
                    "satpsi": 0.355,
                    "slope": 1.0,
                    "scaled_distribution_fn_shape_parameter": 4.05,
                    "multiplier": 0.0,
                    "alpha_fc": 0.33,
                    "Klf": 0.01,
                    "Kn": 0.03,
                    "nash_n": 2,
                    "Cgw": 0.01,
                    "expon": 6.0,
                    "max_groundwater_storage_meters": 1.0,
                    "nash_storage": [
                        0.0,
                        0.0
                    ],
                    "soil_storage_percentage": 0.667,
                    "groundwater_storage_percentage": 0.5,
                    "timestep": 3600
                }
            }
        ],
        "giuh": {
            "giuh_path": "./test/data/giuh/GIUH.json",
            "crosswalk_path": "./data/crosswalk.json"
        },
        "forcing": {
            "file_pattern": ".*{{ID}}.*.csv",
            "path": "./data/forcing/",
            "start_time": "2015-12-01 00:00:00",
            "end_time": "2015-12-30 23:00:00"
        }
    },
    "time": {
        "start_time": "2015-12-01 00:00:00",
        "end_time": "2015-12-30 23:00:00",
        "output_interval": 3600
    },
    "catchments": {
        "tst-1": {
            "formulations": [
                {
                    "name": "tshirt",
                    "params": {
                        "some_param": 4.565028565154633,
                        "maxsmc": 0.439,
                        "wltsmc": 0.066,
                        "satdk": 3.38e-06,
                        "satpsi": 0.355,
                        "slope": 1.0,
                        "scaled_distribution_fn_shape_parameter": 4.05,
                        "multiplier": 0.0,
                        "alpha_fc": 0.33,
                        "Klf": 0.01,
                        "Kn": 0.03,
                        "nash_n": 2,
                        "Cgw": 0.01,
                        "expon": 6.0,
                        "max_groundwater_storage_meters": 1.0,
                        "nash_storage": [
                            0.0,
                            0.0
                        ],
                        "soil_storage_percentage": 0.667,
                        "groundwater_storage_percentage": 0.5,
                        "timestep": 3600
                    }
                }
            ],
            "giuh": {
                "giuh_path": "./test/data/giuh/GIUH.json",
                "crosswalk_path": "./data/crosswalk.json"
            },
            "forcing": {
                "path": "./python/ngen_cal/test/data/cat-87_2015-12-01 00_00_00_2015-12-30 23_00_00.csv",
                "start_time": "2015-12-01 00:00:00",
                "end_time": "2015-12-30 23:00:00"
            },
            "calibration": {"params": [
                {
                    "param": "some_param",
                    "min": 0.0,
                    "max": 1.0,
                    "init": 0.5
                },
                {
                    "param": "maxsmc",
                    "min": 0.2,
                    "max": 1.0,
                    "init": 0.439
                }
            ]}
        }
    }
}
