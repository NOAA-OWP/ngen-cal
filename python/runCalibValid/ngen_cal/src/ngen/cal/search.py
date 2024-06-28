"""
This module contains functions to perform parameter optimization using different algorithms.

@author: Nels Frazer, Xia Feng
"""

import glob
from functools import partial
from math import log
from multiprocessing import pool
import os
import subprocess
from datetime import datetime
from typing import Dict, Optional, Tuple, TYPE_CHECKING

import numpy as np # type: ignore
import pandas as pd # type: ignore

from .gwo_global_best import GlobalBestGWO
from .metric_functions import treat_values, calculate_all_metrics
from .plot_output import plot_calib_output, plot_cost_func
from .utils import pushd, complete_msg 

if TYPE_CHECKING:
    from ngen.cal import Adjustable, Evaluatable
    from ngen.cal.agent import Agent


"""Global private iteration counter

This counter is used by PSO search so that iteration information can be captured
and recorded from within a generic functional representation of an abstract model
managed by a calibration agent.
"""
__iteration_counter = 1


def _execute(meta: 'Agent', i: int = None) -> None:
    """Execute model run via BMI. 

    Parameters
    ----------
    meta : Agent object
    i : Current iteration, default None

    """
    if meta.job.log_file is None:
        subprocess.check_call(meta.cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True, cwd=meta.job.workdir)
    else:
        run_log_file = str(meta.job.log_file)
        if not os.path.exists(run_log_file):
            with open(run_log_file, 'w') as log_file:
                log_file.write('Starting ' + '{}'.format(meta.run_name).capitalize() + ' Run\n')
        if i is not None:
            with open(run_log_file, 'a+') as log_file:
                log_file.write('------ Iteration = {}'.format(i) + ' ------\n')
        with open(run_log_file, 'a+') as log_file:
            subprocess.check_call(meta.cmd, stdout=log_file, stderr=log_file, shell=True, cwd=meta.job.workdir)

def _calc_metrics(
    simulated_hydrograph: pd.Series, 
    observed_hydrograph: pd.Series, 
    eval_range: Tuple[datetime, datetime] = None, 
    threshold: Optional[float] = None,
) -> Dict[str, float]:
    """Calculate statistical metrics.

    Parameters
    ----------
    simulated_hydrograph : Time series of simulated streamflow 
    observed_hydrograph : Time series of observed streamflow 
    eval_range : Evaluation time period for calibration run
    threshold : Streamflow threshold for calculating categorical scores

    Returns
    ----------
    Dictionary of metrics

    """
    df = pd.merge(simulated_hydrograph, observed_hydrograph, left_index=True, right_index=True)
    if df.empty:
        print("WARNING: Cannot compute objective function, do time indicies align?")
    if eval_range:
        df = df.loc[eval_range[0]:eval_range[1]]

    df.reset_index(inplace=True)
    df = treat_values(df, remove_neg = True, remove_na = True)
    obsflow = df['obs_flow']
    simflow = df['sim_flow']

    return calculate_all_metrics(obsflow, simflow, threshold)

def _evaluate(i: int, calibration_object: 'Evaluatable', agent: 'Agent', info: bool=False) -> float:
    """ Calculate objective function and evaluation metrics. 
    Save calibration output and generate plots during iteration. 

    parameters
    ----------
    i : current iteration
    calibration_object : Adjustable object
    agent : Agent object
    info : whether to print objective, best objective and best parameter to screen, default False 

    Returns
    ----------
    Objection funciton at current iteration
 
    """
    # Calculate objective function and metrics
    metrics = _calc_metrics(calibration_object.output, calibration_object.observed, calibration_object.evaluation_range, calibration_object.threshold)
    metric_objective_function = metrics[calibration_object.objective.value.upper()] 
    score = 1 - metric_objective_function if calibration_object.target == 'min' else metric_objective_function 
      
    # Update based on latest objective function and write log files
    calibration_object.update(i, score, log=True, algorithm=agent.algorithm)
    if info:
        print("Current score {}\nBest score {}".format(score, calibration_object.best_score))
        print("Best parameters at iteration {}".format(calibration_object.best_params))

    # Save metrics
    calibration_object.write_metric_iter_file(i, score, metrics)

    # Save params
    calibration_object.write_param_iter_file(i, calibration_object.df[[str(i),'param']])

    # Save output
    calibration_object.save_calib_output(i, str(calibration_object.output_iter_file), str(calibration_object.last_output_file), agent.output_iter_path, 
                                         agent.job.workdir, agent.calib_path_output, calibration_object.save_output_iter_flag)
    calibration_object.save_best_output(str(calibration_object.best_output_file), calibration_object.best_save_flag)

    # Save global and local best cost, and plot
    if len(glob.glob('*.log'))==1 and agent.algorithm !='dds':
        calibration_object.write_cost_iter_file(i, agent.workdir) 

    # Plot metrics, parameters and output
    if len(glob.glob('*.log'))==1 and i%calibration_object.save_plot_iter_freq==0:
        plot_calib_output(i, calibration_object, agent)

    # Save last iteration
    calibration_object.write_last_iteration(i)


def dds_update(iteration: int, inclusion_probability: float, calibration_object: 'Adjustable', agent: 'Agent') -> None:
    """ Dynamically dimensioned search optimization algorithm. 

    parameters
    ----------
    iteration : Current iteration
    inclusion_probability : Probability of each parameter included in neighborhood 
    calibration_object : Adjustable object 
    agent : Agent object

    """
    print( "inclusion probability: {}".format(inclusion_probability) )
    neighborhood = calibration_object.variables.sample(frac=inclusion_probability)
    if neighborhood.empty:
        neighborhood = calibration_object.variables.sample(n=1)
    print( "neighborhood:\n{}".format(neighborhood) )

    # Generate new parameter set by perturbng the best parameters  
    calibration_object.df[str(iteration)] = calibration_object.df[agent.best_params]
    for n in neighborhood:
        new = calibration_object.df.loc[n, agent.best_params] + calibration_object.df.loc[n, 'sigma']*np.random.normal(0,1)
        lower =  calibration_object.df.loc[n, 'min']
        upper = calibration_object.df.loc[n, 'max']
        if new < lower:
            new = lower + (lower - new)
            if new > upper:
                new = lower
        elif new > upper:
            new = upper - (new - upper)
            if new < lower:
                new = upper
        calibration_object.df.loc[n, str(iteration)] = new

    # Fill parameters for all formulations with unique parameter 
    calibration_object.df_fill(iteration)

    # Update realization config file with new parameters 
    agent.update_config(iteration, calibration_object.adf[[str(iteration), 'param', 'model']], calibration_object.id)

def dds(start_iteration: int, iterations: int,  calibration_object: 'Evaluatable', agent: 'Agent')->None:
    """Perform parameter optimization using DDS algorithm.

    Parameters
    ----------
    start_iteration : starting iteration
    iterations : total number of iterations
    agent : Agent object

    """
    if iterations < 2:
        raise(ValueError("iterations must be >= 2"))
    if start_iteration > iterations:
        raise(ValueError("start_iteration must be <= iterations"))

    init = start_iteration - 1 if start_iteration > 0 else start_iteration
    neighborhood_size = agent.parameters.get('neighborhood', 0.2)
    calibration_object.df['sigma'] = neighborhood_size*(calibration_object.df['max'] - calibration_object.df['min'])
    agent.update_config(init, calibration_object.df[[str(init), 'param', 'model']], calibration_object.id)

    # Produce baseline simulation output using the default parameter set
    if start_iteration == 0:
        if calibration_object.output is None:
            print("Running {} to produce initial simulation".format(agent.cmd))
            agent.update_config(start_iteration, calibration_object.df[[str(start_iteration), 'param', 'model']], calibration_object.id)
            _execute(agent, start_iteration)
        with pushd(agent.job.workdir):
            _evaluate(0, calibration_object, agent, info=True)
        calibration_object.check_point(agent.job.workdir)
        start_iteration += 1

    for i in range(start_iteration, iterations+1):
        # Calculate probability of inclusion
        inclusion_probability = 1 - log(i)/log(iterations)
        dds_update(i, inclusion_probability, calibration_object, agent)
        # Run cmd 
        print("Running {} for iteration {}".format(agent.cmd, i))
        _execute(agent, i)
        with pushd(agent.job.workdir):
            _evaluate(i, calibration_object, agent)
        calibration_object.check_point(agent.job.workdir)

def dds_set(start_iteration: int, iterations: int, agent: 'Agent')->None:
    """Perform parameter optimization using DDS algorithm.

    parameters
    ----------
    start_iteration : starting iteration
    iterations : total number of iterations
    agent : Agent object

    """
    # TODO I think the can ultimately be refactored and merged with dds, there only a couple very
    # minor differenes in this implementation, and I think those can be abstrated away
    # by carefully crafting sets and adjustables before this function is ever reached.
    if iterations < 2:
        raise(ValueError("iterations must be >= 2"))
    if start_iteration > iterations:
        raise(ValueError("start_iteration must be <= iterations"))

    neighborhood_size = agent.parameters.get('neighborhood', 0.2)
    calibration_sets = agent.model.adjustables
    init = start_iteration - 1 if start_iteration > 0 else start_iteration

    for calibration_set in calibration_sets:
        for calibration_object in calibration_set.adjustables:
            calibration_object.df['sigma'] = neighborhood_size*(calibration_object.df['max'] - calibration_object.df['min'])
            #TODO optimize by passing the set and iterating in update, then only have to write once to file
            calibration_object.df_fill(init)
            agent.update_config(init, calibration_object.adf[[str(init), 'param', 'model']], calibration_object.id)

        # Produce baseline simulation output using the default parameter set
        if start_iteration == 0:
            if calibration_set.output is None:
                print("Running {} to produce initial simulation".format(agent.cmd))
                _execute(agent, start_iteration)
            with pushd(agent.job.workdir):
                _evaluate(0, calibration_set, agent, info=True)
            calibration_set.check_point(agent.job.workdir)
            start_iteration += 1

        for i in range(start_iteration, iterations+1):
            # Calculate probability of inclusion
            inclusion_probability = 1 - log(i)/log(iterations)
            for calibration_object in calibration_set.adjustables:
                dds_update(i, inclusion_probability, calibration_object, agent)

            # Execute model run 
            print("Running {} for iteration {}".format(agent.cmd, i))
            _execute(agent, i)
            with pushd(agent.job.workdir):
                _evaluate(i, calibration_set, agent)
            calibration_set.check_point(agent.job.workdir)

        # Create configuration files for validation run
        calibration_object.create_valid_realization_file(agent, calibration_object.adf)

        # Indicate completion
        calibration_object.write_run_complete_file(agent.run_name, agent.workdir)
        complete_msg(calibration_object.basinID, agent.run_name, agent.workdir, calibration_object.user)

def compute(calibration_object: 'Adjustable', iteration: int, input: Tuple) -> float:
    """Execute run and evaluate objection function.

    parameters
    ----------
    calibration_object : Adjustable object
    iteration : starting iteration
    input : Agent and associated parameters 

    """
    params = input[0]
    agent = input[1]
    
    # Execute run with the updated parameter set and evaluate objective function
    calibration_object.df[str(iteration)] = params
    with pushd(agent.job.workdir):
        agent.update_config(iteration, calibration_object.df[[str(iteration), 'param', 'model']], calibration_object.id)
        _execute(agent, iteration)
        cost = _evaluate(iteration, calibration_object, agent)
        calibration_object.check_point(agent.job.workdir)
    return cost

def cost_func( calibration_object: 'Adjustable', agents: 'Agent', pool: int, params: pd.DataFrame):
    """Compute cost function for each iteration.

    Parameters:
    ----------
    calibration_object : Adjustable object
    agents : Agent object
    pool : Pool size
    params : Parameter set

    Returns:
    ----------

    """
    global __iteration_counter
    #TODO implement multi-processing here???
    func = partial(compute, calibration_object, __iteration_counter)
    costs = np.fromiter(pool.imap(func, zip(params, agents)), dtype=float)
    __iteration_counter = __iteration_counter + 1

    return costs

def pso_search(start_iteration: int, iterations: int,  agent: 'Agent') -> None:
    """Search optimal parameter set using PSO algorithm. 

    parameters
    ----------
    start_iteration : starting iteration
    iterations : total number of iterations 
    agent : Agent object 

    """
    import pyswarms as ps

    # Utilizing PSO optimizers requires n "particles" to run -- so we need to take the existing meta
    # and create a unique copy customized for each particle, so then each one gets an execution/update
    num_particles = agent.parameters.get('particles', 4)
    pool_size = agent.parameters.get("pool", 1)
    print("Running PSO with {} particles using {} processes".format(num_particles, pool_size))

    #TODO warn about potential loss of data when particles > pool
    _pool = pool.Pool(pool_size)
    agents = [agent] + [ agent.duplicate() for i in range(num_particles-1) ]
    default_options = {'c1': 0.5, 'c2': 0.3, 'w':0.9}
    options = agent.parameters.get("options", default_options)
    for calibration_object in agent.model.adjustables:
        #Produce the baseline simulation output for first agent
        if start_iteration == 0:
            if calibration_object.output is None:
                print("Running {} to produce initial simulation".format(agent.cmd))
                agent.update_config(start_iteration, calibration_object.df[[str(start_iteration), 'param', 'model']], calibration_object.id)
                _execute(agent, start_iteration)
            with pushd(agent.job.workdir):
                _evaluate(0, calibration_object, agent, info=True)
            calibration_object.check_point(agent.job.workdir)
        bounds = calibration_object.bounds
        bounds = (bounds[0].values, bounds[1].values)

        # Call instance of PSO
        # TODO hook other pyswarm algorithms by user selection
        # TODO hook swarmpackagepy algorithms by user selection (they follow a very similar functional pattern)
        # A quick look at swarmpackagepy shows that it might be a little more challenging since it does this to update states:
        """
            Pbest = self.__agents[
                np.array([function(x) for x in self.__agents]).argmin()]
            if function(Pbest) < function(Gbest):
                Gbest = Pbest
        """
        # meaning that the cost_func is called multiple time PER ITERATION, which doesn't coincide with the architecture
        # we are using here to interface with pyswarm, which only calls the cost_func once per iteration, and tracks other states internally
        # this is a significant problem, especially considering the computation costs of our "cost_function"
        optimizer = ps.single.GlobalBestPSO(n_particles=num_particles, dimensions=len(calibration_object.df), options=options, bounds=bounds)
        cf = partial(cost_func, calibration_object, agents, _pool)

        # Perform optimization
        # For pyswarm, DO NOT use the embedded multi-processing -- it is impossible to track the mapping of an agent to the params
        cost, pos = optimizer.optimize(cf, iters=iterations, n_processes=None)
        calibration_object.df.loc[:,'global_best'] = pos
        calibration_object.check_point(agent.workdir)
        print("Best params with cost {}:".format(cost))
        print(calibration_object.df[['param','global_best']].set_index('param'))

        # Save and plot history  
        cost_hist_file = calibration_object.write_hist_file(optimizer, agent, list(calibration_object.df['param']))
        plot_cost_func(calibration_object, agent, cost_hist_file, agent.algorithm)

        # Create configuration files for validation run
        calibration_object.create_valid_realization_file(agent, calibration_object.df) 

        # Indicate completion 
        calibration_object.write_run_complete_file(agent.run_name, agent.workdir)
        complete_msg(calibration_object.basinID, agent.run_name, agent.workdir, calibration_object.user)

def gwo_search(start_iteration: int, iterations: int,  agent)->None:
    """Search optimal parameter set using GWO algorithm.  

    parameters
    ----------
    start_iteration : start iteration
    iterations : total number of iterations 
    agent : Agent object 

    """
    global __iteration_counter
    __iteration_counter = start_iteration + 1 if start_iteration==0 else start_iteration
    print("_iteration_counter is", __iteration_counter)
    num_particles = agent.parameters.get('particles', 10)
    pool_size = agent.parameters.get("pool", num_particles)
    print("Running GWO with {} particles using {} processes".format(num_particles, pool_size))
    _pool = pool.Pool(pool_size)
    if start_iteration ==0:
        agents = [agent] + [ agent.duplicate() for i in range(num_particles-1) ]
    else:
        agents = [agent] + [ agent.duplicate(restart_flag=True, agent_counter=i+1) for i in range(num_particles-1) ]
        for agent in agents:
            if len(glob.glob(os.path.join(agent.job.workdir, '*.log')))!=1:
                agent.restart()
    for calibration_object in agent.model.adjustables:
        #Produce the baseline simulation output for first agent
        if start_iteration == 0:
            if calibration_object.output is None:
                print("Running {} to produce initial simulation".format(agent.cmd))
                agent.update_config(start_iteration, calibration_object.df[[str(start_iteration), 'param', 'model']], calibration_object.id)
                _execute(agent, start_iteration)
            with pushd(agent.job.workdir):
                _evaluate(0, calibration_object, agent, info=True)
            calibration_object.check_point(agent.job.workdir)
        bounds = calibration_object.bounds
        bounds = (bounds[0].values, bounds[1].values)

        # Initialize swarms 
        optimizer = GlobalBestGWO(n_particles=num_particles, dimensions=len(calibration_object.df), bounds=bounds, start_iter=start_iteration,
                                  calib_path=agent.calib_path, basinid=calibration_object.basinID)
        cf = partial(cost_func, calibration_object, agents, _pool)

        # Perform optimization
        cost, pos = optimizer.optimize(cf, iters=iterations, n_processes=None)
        calibration_object.df.loc[:,'global_best'] = pos
        calibration_object.check_point(agent.workdir)
        print("Best params with cost {}:".format(cost))
        print(calibration_object.df[['param','global_best']].set_index('param'))

        # Save and plot history
        cost_hist_file = calibration_object.write_hist_file(optimizer, agent, list(calibration_object.df['param']))
        plot_cost_func(calibration_object, agent, cost_hist_file, agent.algorithm)

        # Create configuration files for validation run
        calibration_object.create_valid_realization_file(agent, calibration_object.df)

        # Indicate completion
        calibration_object.write_run_complete_file(agent.run_name, agent.workdir)
        complete_msg(calibration_object.basinID, agent.run_name, agent.workdir, calibration_object.user)
