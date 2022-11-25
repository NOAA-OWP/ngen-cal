import subprocess
import pandas as pd # type: ignore
from math import log
import numpy as np # type: ignore
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ngen.cal import Adjustable, Evaluatable, CalibrationMeta, CalibrationSet

from ngen.cal.objectives import custom

def _objective_func(simulated_hydrograph, observed_hydrograph, objective, eval_range=None):
    df = pd.merge(simulated_hydrograph, observed_hydrograph, left_index=True, right_index=True)
    if df.empty:
        print("WARNING: Cannot compute objective function, do time indicies align?")
    if eval_range:
        df = df.loc[eval_range[0]:eval_range[1]]
    #print( df )
    #Evaluate custom objective function providing simulated, observed series
    return objective(df['obs_flow'], df['sim_flow'])

def _execute(meta: 'CalibrationMeta'):
    """
        Execute a model run defined by the calibration meta cmd
    """
    if meta.log_file is None:
        subprocess.check_call(meta.cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True, cwd=meta.workdir)
    else:
        with open(meta.log_file, 'a+') as log_file:
            subprocess.check_call(meta.cmd, stdout=log_file, stderr=log_file, shell=True, cwd=meta.workdir)

def _evaluate(i: int, calibration_object: 'Evaluatable', meta: 'CalibrationMeta'):
    """
        Performs the evaluation logic of a calibration step
    """

    #read output and calculate objective_func
    score =  _objective_func(calibration_object.output, calibration_object.observed, calibration_object.objective, calibration_object.evaluation_range)
    #save the calibration state, just in case
    calibration_object.save_output(i)
    #update meta info based on latest score and write some log files
    meta.update(i, score, log=True)

    print("Current score {}\nBest score {}".format(score, calibration_object.best_score))
    print("Best parameters at iteration {}".format(calibration_object.best_params))

def dds_update(iteration: int, inclusion_probability: float, calibration_object: 'Adjustable', meta: 'CalibrationMeta'):
    """_summary_

    Args:
        iteration (int): _description_
    """

    print( "inclusion probability: {}".format(inclusion_probability) )
    #select a random subset of variables to modify
    #TODO convince myself that grabbing a random selction of P fraction of items
    #is the same as selecting item with probability P
    neighborhood = calibration_object.variables.sample(frac=inclusion_probability)
    if neighborhood.empty:
        neighborhood = calibration_object.variables.sample(n=1)
    print( "neighborhood: {}".format(neighborhood) )
    #Copy the best parameter values so far into the next iterations parameter list
    calibration_object.df[str(iteration)] = calibration_object.df[meta.best_params]
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
        calibration_object.df.loc[n, str(iteration)] = new
    """
        At this point, we need to re-run cmd with the new parameters assigned correctly and evaluate the objective function
    """
    #Update the meta info and prepare for next iteration
    #Pass the parameter and interation columns of the object we are calibrating to the update function
    meta.update_config(iteration, calibration_object.df[[str(iteration), 'param', 'model']], calibration_object.id)


def dds(start_iteration: int, iterations: int,  calibration_object: 'Adjustable', meta: 'CalibrationMeta'):
    """
    """
    if iterations < 2:
        raise(ValueError("iterations must be >= 2"))
    if start_iteration > iterations:
        raise(ValueError("start_iteration must be <= iterations"))
    #TODO make this a parameter
    neighborhood_size = 0.2

    #precompute sigma for each variable based on neighborhood_size and bounds
    calibration_object.df['sigma'] = neighborhood_size*(calibration_object.df['max'] - calibration_object.df['min'])
    
    #Produce the baseline simulation output
    if start_iteration == 0:
        if calibration_object.output is None:
            #We are starting a new calibration and do not have an initial output state to evaluate, compute it
            #Need initial states  (iteration 0) to start DDS loop
            print("Running {} to produce initial simulation".format(meta.cmd))
            _execute(meta)
        _evaluate(0, calibration_object, meta)
        calibration_object.check_point(meta.workdir)
        start_iteration += 1

    for i in range(start_iteration, iterations+1):
        #Calculate probability of inclusion
        inclusion_probability = 1 - log(i)/log(iterations)
        dds_update(i, inclusion_probability, calibration_object, meta)
        #Run cmd Again...
        print("Running {} for iteration {}".format(meta.cmd, i))
        _execute(meta)
        _evaluate(i, calibration_object, meta)
        calibration_object.check_point(meta.workdir)

def dds_set(start_iteration: int, iterations: int,  calibration_set: 'CalibrationSet', meta: 'CalibrationMeta'):
    """
        DDS search that applies to a set of calibration objects.

        This works by giving each object a parameter space, but allows a single execution
        step to happen each iteration, and then each object in the set can be adjusted independently
        and then evaluated as a whole.
    """
    # TODO I think the can ultimately be refactored and merged with dds, there only a couple very
    # minor differenes in this implementation, and I think those can be abstrated away
    # by carefully crafting sets and adjustables before this function is ever reached.
    if iterations < 2:
        raise(ValueError("iterations must be >= 2"))
    if start_iteration > iterations:
        raise(ValueError("start_iteration must be <= iterations"))
    #TODO make this a parameter
    neighborhood_size = 0.2

    for calibration_object in calibration_set.adjustables:
        #precompute sigma for each variable based on neighborhood_size and bounds
        calibration_object.df['sigma'] = neighborhood_size*(calibration_object.df['max'] - calibration_object.df['min'])
    
    #Produce the baseline simulation output
    if start_iteration == 0:
        if calibration_set.output is None:
            #We are starting a new calibration and do not have an initial output state to evaluate, compute it
            #Need initial states  (iteration 0) to start DDS loop
            print("Running {} to produce initial simulation".format(meta.cmd))
            _execute(meta)
        _evaluate(0, calibration_set, meta)
        calibration_set.check_point(meta.workdir)
        start_iteration += 1

    for i in range(start_iteration, iterations+1):
        #Calculate probability of inclusion
        inclusion_probability = 1 - log(i)/log(iterations)
        for calibration_object in calibration_set.adjustables:
            dds_update(i, inclusion_probability, calibration_object, meta)
        #Run cmd Again...
        print("Running {} for iteration {}".format(meta.cmd, i))
        _execute(meta)
        _evaluate(i, calibration_set, meta)
        calibration_set.check_point(meta.workdir)
