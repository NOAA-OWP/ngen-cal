import subprocess
import pandas as pd
from math import log
import numpy as np
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ngen_cal import Calibratable, CalibrationMeta

from ngen_cal.objectives import custom

def _objective_func(simulated_hydrograph, observed_hydrograph, eval_range=None):
    df = pd.merge(simulated_hydrograph, observed_hydrograph, left_index=True, right_index=True)
    if df.empty:
        print("WARNING: Cannot compute objective function, do time indicies align?")
    if eval_range:
        df = df.loc[eval_range[0]:eval_range[1]]
    #print( df )
    #Evaluate custom objective function providing simulated, observed series
    return custom(df['sim_flow'], df['obs_flow'])

def _execute(meta: 'CalibrationMeta'):
    """
        Execute a model run defined by the calibration meta cmd
    """
    with open(meta.log_file, 'a') as log_file:
        subprocess.check_call(meta.cmd, stdout=log_file, shell=True)

def _evaluate(i: int, calibration_object: 'Calibratable', meta: 'CalibrationMeta'):
    """
        Performs the evaluation logic of a calibration step
    """

    #read output and calculate objective_func
    score =  _objective_func(calibration_object.output, calibration_object.observed)
    #save the calibration state, just in case
    calibration_object.save_output(i)
    #update meta info based on latest score and write some log files
    meta.update(i, score, log=True)

    print("Current score {}\nBest score {}".format(score, meta.best_score))
    calibration_object.check_point(meta.workdir)

    print("Best parameters at iteration {}".format(meta.best_params))

def dds(start_iteration: int, iterations: int, calibration_object: 'Calibratable', meta: 'CalibrationMeta'):
    """
        Functional form of the dds loop
    """
    if iterations < 2:
        raise(ValueError("iterations must be >= 2"))
    if start_iteration > iterations:
        raise(ValueError("start_iteration must be <= iterations"))
    #TODO make this a parameter
    neighborhood_size = 0.2

    #precompute sigma for each variable based on neighborhood_size and bounds
    calibration_object.df['sigma'] = neighborhood_size*(calibration_object.df['max'] - calibration_object.df['min'])

    if start_iteration == 0:
        if calibration_object.output is None:
            #We are starting a new calibration and do not have an initial output state to evaluate, compute it
            #Need initial states  (iteration 0) to start DDS loop
            print("Running {} to produce initial simulation".format(meta.cmd))
            _execute(meta)
        _evaluate(0, calibration_object, meta)
        start_iteration += 1

    for i in range(start_iteration, iterations+1):
        #Calculate probability of inclusion
        inclusion_probability = 1 - log(i)/log(iterations)
        print( "inclusion probability: {}".format(inclusion_probability) )
        #select a random subset of variables to modify
        #TODO convince myself that grabbing a random selction of P fraction of items
        #is the same as selecting item with probability P
        neighborhood = calibration_object.variables.sample(frac=inclusion_probability)
        if neighborhood.empty:
           neighborhood = calibration_object.variables.sample(n=1)
        print( "neighborhood: {}".format(neighborhood) )
        #Copy the best parameter values so far into the next iterations parameter list
        calibration_object.df[str(i)] = calibration_object.df[meta.best_params]
        #print( data.calibration_df )
        for n in neighborhood:
            #permute the variables in neighborhood
            #using a random normal sample * sigma, sigma = 0.2*(max-min)
            #print(n, meta.best_params)
            new = calibration_object.df.loc[n, meta.best_params] + calibration_object.df.loc[n, 'sigma']*np.random.normal(0,1)
            lower =  calibration_object.df.loc[n, 'min']
            upper = calibration_object.df.loc[n, 'max']
            #print( new )
            #print( lower )
            #print( upper )
            if new < lower:
                new = lower + (lower - new)
                if new > upper:
                    new = lower
            elif new > upper:
                new = upper - (new - upper)
                if new < lower:
                    new = upper
            calibration_object.df.loc[n, str(i)] = new
        """
            At this point, we need to re-run cmd with the new parameters assigned correctly and evaluate the objective function
        """
        #Update the meta info and prepare for next iteration
        meta.update_config(i)
        #Run cmd Again...
        print("Running {} for iteration {}".format(meta.cmd, i))
        _execute(meta)
        _evaluate(i, calibration_object, meta)
