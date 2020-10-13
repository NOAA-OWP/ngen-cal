import json
import pandas as pd

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class CalibrationMeta:
    """
        Structure for holding calibration meta data

        ###TODO can we hold enough `configuration` information to make it possible to update global config
    """

    def __init__(self, config, workdir, bin, args, id):
        """

        """
        self._config = config #This is the Configuration object that knows how to operate on model configuration files
        self._workdir = workdir
        self._best_score = -1
        self._best_params_iteration = '0' #String representation of interger iteration
        self._bin = bin
        self._args = args
        self._log_file = self._workdir/"{}_log_file".format(bin)
        self._id = id #a unique identifier to prepend to log files
        #FIXME another reason to refactor meta under catchment, logs per catchment???

        self._param_log_file = self._workdir/"{}_best_params.log".format(self._id)
        self._objective_log_file = self._workdir/"{}_objective.log".format(self._id)

    def update_config(self, i: int, params: 'DataFrame', cat_id: str):
        """
            For a given calibration iteration, i, update the input files/configuration to prepare for that iterations
            calibration run.

            parameters
            ---------
            i: int
                current iteration of calibration
            params: pandas.DataFrame
                DataFrame containing the parameter name in `param` and value in `i` columns
        """

        #extract parameters from Pandas DataFrame data to update JSON configuration file 
        #for next round of iteration run
        print(params, "\n")
        """
        # extracting parameter name and value columns from a dataframe params and convert to dict for easy access
        # assuming the column order is (param, i)
        param_dict = dict()
        for idx, p in params.iterrows():
            print("idx = {}".format(idx))
            print("params column name and values = {}".format(p.values))
            #print("params column name and values = {}".format(p.values[0]))    # use for calibration.csv with no commas
            #p_list = (p.values[0]).split()    # use for calibration.csv with no commas, this insert a comma between values
            p_list = p.values
            print("p_list = {}".format(p_list))
            dict_tmp = {p_list[0]: float(p_list[-1])}
            param_dict.update(dict_tmp)
            print("p_list[2] = {}".format(p_list[2]))
            print(dict_tmp)
        """

        # extracting parameter value and name columns from a dataframe params and convert to dict for easy access
        # assuming the column order is (i, param)
        param_dict = dict()
        for idx, p in params.iterrows():
            dict_tmp = {(p.values[-1]).strip(): float(p.values[0])}
            print("dict_tmp = {}".format(dict_tmp))
            param_dict.update(dict_tmp)

        # print out the extracted parameters in dictionary form
        print("\nparam_dict:", param_dict)
        print("\n")

        # update the config file using the best estimate for parameters in the last calibration step
        # calibration_config.json is the input file containing the calibration parameters for te catchments
        #config_file = "calibration_config.json"
        config_file = Configuration(config_file, '')
        config_in = config_file
        #using alternative config_in, check that the output can be read back in
        #config_file = "config_out1.json"

        # read in the config file from last calibration step
        #with open(config_file) as fp:
        with open(config_in) as fp:
            data = json.load(fp)

        #save a copy of the input config file before update, rename
        config_keep = "config_" + cat_id + "." + "json"
        with open(config_keep, 'w') as f:  # writing JSON object
            json.dump(data, f)

        #new_param = {"maxsmc": 0.439, "satdk":0.00000338, "refkdt":3.0, "slope":0.01, "bb":4.05, "multiplier":100.0, "expon":6.0}
        new_param = param_dict

        # update calibration parameters in data in json format
        # during the calibration iteration process, the dataframe file is updated each iteration step
        # and returned to be used for next iteration as input parameters
        #for id, params in data['catchments']['cat-87'].items():
        for id, params in data['catchments'][cat_id].items():
            print("id, params = {}, {}\n".format(id,params))
            for param in params:
                param['init'] = new_param[param['param']]

        # write to a json file
        #config_out = "config_out"
        #config_out = config_out + "_" + str(i) + "." + "json"
        #with open('config_out.json', 'w') as f:
        config_out = config_file
        with open(config_out, 'w') as f:
            json.dump(data, f)


    @property
    def workdir(self) -> 'Path':
        return self._workdir

    @property
    def best_score(self) -> float:
        """
            Best score known to the current calibration
        """
        return self._best_score

    @property
    def best_params(self) -> str:
        """
            The integer iteration that contains the best parameter values, as a string
        """
        return self._best_params_iteration

    @property
    def cmd(self) -> str:
        """

        """
        return "{} {}".format(self._bin, self._args)

    @property
    def log_file(self) -> 'Path':
        """

        """
        return self._workdir/self._log_file

    def update(self, i: int, score: int, log: bool):
        """
            Update the meta state for iteration `i` having score `score`
            logs parameter and objective information if log=True
        """
        if score <= self.best_score:
            self._best_params_iteration = i
            self._best_score = score

        if log:
            self.write_param_log_file(i)
            self.write_objective_log_file(i, score)

    def write_objective_log_file(self, i, score):
        with open(self._objective_log_file, 'a') as log_file:
            log_file.write('{}, '.format(i))
            log_file.write('{}\n'.format(score))

    def write_param_log_file(self, i):
        with open(self._param_log_file, 'w') as log_file:
            log_file.write('{}\n'.format(i))
            log_file.write('{}\n'.format(self.best_params))
            log_file.write('{}\n'.format(self.best_score))

    def read_param_log_file(self):
        with open(self._param_log_file, 'r') as log_file:
            iteration = int(log_file.readline())
            best_params = int(log_file.readline())
            best_score = float(log_file.readline())
        return iteration, best_params, best_score

    def restart(self) -> int:
        """
            Attempt to restart a calibration from a previous state.
            If no previous state is available, start from 0

            Returns
            -------
            int iteration to start calibration at
        """
        #TODO how much meta info is catchment specific vs global?  Might want to wrap this up per catchment?
        try:
            last_iteration, best_params, best_score = self.read_param_log_file()
            self._best_params_iteration = str(best_params)
            self._best_score = best_score
            start_iteration = last_iteration + 1

            for catchment in self._config.catchments:
                catchment.load_df()
            #TODO verify that loaded calibration info aligns with iteration?  Anther reason to consider making this meta
            #per catchment???

        except FileNotFoundError:
            start_iteration = 0

        return start_iteration
