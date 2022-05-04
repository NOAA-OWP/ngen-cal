from pathlib import Path
_where = str(Path(__file__).parent)
config = {
        "global": {
        "formulations": [
            {
                "name": "tshirt",
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
                    "timestep": 3600,
                    "giuh": {
                        "giuh_path": _where+"/data/giuh/GIUH.json",
                        "crosswalk_path": _where+"/data/crosswalk.json"
                    },
                }
            }
        ],
        "forcing": {
            #FIXME regex not working???
            #"file_pattern": ".*{{ID}}.*csv",
            "path":_where+"/data/cat-87_2015-12-01 00_00_00_2015-12-30 23_00_00.csv",
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
                        "timestep": 3600,
                        "giuh": {
                            "giuh_path": _where+"/data/giuh/GIUH.json",
                            "crosswalk_path": _where+"/data/crosswalk.json"
                        }
                    }
                }
            ],
            "forcing": {
                "path": _where+"/data/cat-87_2015-12-01 00_00_00_2015-12-30 23_00_00.csv",
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

algorithm_good = {"algorithm": "dds"}
algorithm_bad = {"algorithm": "foo"}

strategy_estimation = {"type": "estimation", **algorithm_good}
strategy_sensitivity = {"type": "sensitivity"}

general_no_defaults = {"strategy":strategy_estimation, 
                    "iterations": 10,
                    "evaluation_start": "2015-12-01 00:00:00", 
                    "evaluation_stop": "2015-12-30 23:00:00",
                    "restart": True,
                    "start_iteration": 5,
                    "workdir": "/tmp",
                    "log_file": "test_log",
                    "parameter_log_file": "test_param_log",
                    "objectective_log_file": "test_obj_log"}

general_w_defaults = {"strategy":strategy_estimation, 
                    "iterations": 10,
                    "evaluation_start": "2015-12-01 00:00:00", 
                    "evaluation_stop": "2015-12-30 23:00:00"}

model_params = {"binary":"echo", "args":"ngen args"}
