from __future__ import annotations

import subprocess
import pandas as pd # type: ignore
from math import log
import numpy as np # type: ignore
from typing import TYPE_CHECKING
from functools import partial
from multiprocessing import pool
from ngen.cal.utils import pushd
if TYPE_CHECKING:
    from ngen.cal import Adjustable, Evaluatable
    from ngen.cal.agent import Agent
    from typing import Tuple, Optional
    from datetime import datetime


"""Global private iteration counter

This counter is used by PSO search so that iteration information can be captured
and recorded from within a generic functional representation of an abstract model
managed by a calibration agent.
"""
__iteration_counter = 0

def _objective_func(simulated_hydrograph, observed_hydrograph, objective, eval_range: 'Optional[Tuple[datetime, datetime]]' = None):
    df = pd.merge(simulated_hydrograph, observed_hydrograph, left_index=True, right_index=True)
    if df.empty:
        print("WARNING: Cannot compute objective function, do time indicies align?")
    if eval_range:
        df = df.loc[eval_range[0]:eval_range[1]]
    #print( df )
    #Evaluate custom objective function providing simulated, observed series
    return objective(df['obs_flow'], df['sim_flow'])

def _execute(meta: 'Agent'):
    """
        Execute a model run defined by the calibration meta cmd
    """
    if meta.job.log_file is None:
        subprocess.check_call(meta.cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True, cwd=meta.job.workdir)
    else:
        with open(meta.job.log_file, 'a+') as log_file:
            subprocess.check_call(meta.cmd, stdout=log_file, stderr=log_file, shell=True, cwd=meta.job.workdir)

def _evaluate(i: int, calibration_object: 'Evaluatable', info=False) -> float:
    """
        Performs the evaluation logic of a calibration step
    """

    #read output and calculate objective_func
    score =  _objective_func(calibration_object.output, calibration_object.observed, calibration_object.objective, calibration_object.evaluation_range)
    #update meta info based on latest score and write some log files
    calibration_object.update(i, score, log=True)
    if info:
        print(f"Current score {score}\nBest score {calibration_object.best_score}")
        print(f"Best parameters at iteration {calibration_object.best_params}")
    return score

def dds_update(iteration: int, inclusion_probability: float, calibration_object: 'Adjustable', agent: 'Agent'):
    """_summary_

    Args:
        iteration (int): _description_
    """

    print( f"inclusion probability: {inclusion_probability}" )
    #select a random subset of variables to modify
    #TODO convince myself that grabbing a random selction of P fraction of items
    #is the same as selecting item with probability P
    neighborhood = calibration_object.variables.sample(frac=inclusion_probability)
    if neighborhood.empty:
        neighborhood = calibration_object.variables.sample(n=1)
    print( f"neighborhood: {neighborhood}" )
    #Copy the best parameter values so far into the next iterations parameter list
    calibration_object.df[str(iteration)] = calibration_object.df[agent.best_params]
    #print( data.calibration_df )
    for n in neighborhood:
        #permute the variables in neighborhood
        #using a random normal sample * sigma, sigma = 0.2*(max-min)
        #print(n, meta.best_params)
        new = calibration_object.df.loc[n, agent.best_params] + calibration_object.df.loc[n, 'sigma']*np.random.normal(0,1)
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
    agent.update_config(iteration, calibration_object.df[[str(iteration), 'param', 'model']], calibration_object.id)


def dds(start_iteration: int, iterations: int,  calibration_object: 'Evaluatable', agent: 'Agent'):
    """
    """
    if iterations < 2:
        raise(ValueError("iterations must be >= 2"))
    if start_iteration > iterations:
        raise(ValueError("start_iteration must be <= iterations"))

    init = start_iteration - 1 if start_iteration > 0 else start_iteration
    neighborhood_size = agent.parameters.get('neighborhood', 0.2)

    #precompute sigma for each variable based on neighborhood_size and bounds
    calibration_object.df['sigma'] = neighborhood_size*(calibration_object.df['max'] - calibration_object.df['min'])
    agent.update_config(init, calibration_object.df[[str(init), 'param', 'model']], calibration_object.id)

    #Produce the baseline simulation output
    if start_iteration == 0:
        if calibration_object.output is None:
            #We are starting a new calibration and do not have an initial output state to evaluate, compute it
            #Need initial states  (iteration 0) to start DDS loop
            print(f"Running {agent.cmd} to produce initial simulation")
            agent.update_config(start_iteration, calibration_object.df[[str(start_iteration), 'param', 'model']], calibration_object.id)
            _execute(agent)
        with pushd(agent.job.workdir):
            _evaluate(0, calibration_object, info=True)
        calibration_object.check_point(0, agent.job)
        start_iteration += 1

    for i in range(start_iteration, iterations+1):
        #Calculate probability of inclusion
        inclusion_probability = 1 - log(i)/log(iterations)
        dds_update(i, inclusion_probability, calibration_object, agent)
        #Run cmd Again...
        print(f"Running {agent.cmd} for iteration {i}")
        _execute(agent)
        with pushd(agent.job.workdir):
            _evaluate(i, calibration_object, info=True)
        calibration_object.check_point(i, agent.job)

def dds_set(start_iteration: int, iterations: int, agent: 'Agent'):
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

    neighborhood_size = agent.parameters.get('neighborhood', 0.2)
    
    calibration_sets = agent.model.adjustables
    init = start_iteration - 1 if start_iteration > 0 else start_iteration
    for calibration_set in calibration_sets:
        for calibration_object in calibration_set.adjustables:
            #precompute sigma for each variable based on neighborhood_size and bounds
            calibration_object.df['sigma'] = neighborhood_size*(calibration_object.df['max'] - calibration_object.df['min'])
            #TODO optimize by passing the set and iterating in update, then only have to write once to file
            agent.update_config(init, calibration_object.df[[str(init), 'param', 'model']], calibration_object.id)

        #Produce the baseline simulation output
        if start_iteration == 0:
            if calibration_set.output is None:
                #We are starting a new calibration and do not have an initial output state to evaluate, compute it
                #Need initial states  (iteration 0) to start DDS loop
                print(f"Running {agent.cmd} to produce initial simulation")
                _execute(agent)
            with pushd(agent.job.workdir):
                _evaluate(0, calibration_set, info=True)
            calibration_set.check_point(0, agent.job)
            start_iteration += 1

        for i in range(start_iteration, iterations+1):
            #Calculate probability of inclusion
            inclusion_probability = 1 - log(i)/log(iterations)
            for calibration_object in calibration_set.adjustables:
                dds_update(i, inclusion_probability, calibration_object, agent)
            #Run cmd Again...
            print(f"Running {agent.cmd} for iteration {i}")
            _execute(agent)
            with pushd(agent.job.workdir):
                _evaluate(i, calibration_set, info=True)
            calibration_set.check_point(i, agent.job)

def compute(calibration_object, iteration, input) -> float:
    params = input[0]
    agent = input[1]
    
    #Update the meta info and prepare for next iteration
    #Pass the parameter and interation columns of the object we are calibrating to the update function
    calibration_object.df[str(iteration)] = params
    #print(calibration_object.df[str(iteration)])
    with pushd(agent.job.workdir):
        agent.update_config(iteration, calibration_object.df[[str(iteration), 'param', 'model']], calibration_object.id)
        _execute(agent)
        cost = _evaluate(iteration, calibration_object)
        calibration_object.check_point(iteration, agent.job)
        #cost = _objective_func(calibration_object.output, calibration_object.observed, calibration_object.objective, calibration_object.evaluation_range)
    return cost

def cost_func( calibration_object: 'Adjustable', agents: 'Agent', pool, params):
    """_summary_

    Args:
        meta (CalibrationMeta): _description_
        calibration_object (Adjustable): _description_
        params (_type_): _description_
    """
    global __iteration_counter
    #TODO implement multi-processing here???
    func = partial(compute, calibration_object, __iteration_counter)
    costs = np.fromiter(pool.imap(func, zip(params, agents)), dtype=float)
    # for r in :
    #     costs.append(r)
    #Update global iteration counter 
    __iteration_counter = __iteration_counter + 1

    return costs

def pso_search(start_iteration: int, iterations: int,  agent):
    """_summary_

    Args:
        start_iteration (int): _description_
        iterations (int): _description_
        calibration_set (CalibrationSet): _description_
        meta (CalibrationMeta): _description_
    """
    import pyswarms as ps

    """
        Utilizing PSO optimizers requires n "particles" to run -- so we need to take the existing meta
        and create a unique copy customized for each particle, so then each one gets an execution/update
    """

    #TODO run first iteration?
    num_particles = agent.parameters.get('particles', 4)
    pool_size = agent.parameters.get("pool", 1)
    print(f"Running PSO with {num_particles} particles using {pool_size} processes")
    #TODO warn about potential loss of data when particles > pool
    _pool = pool.Pool(pool_size)
    agents = [agent] + [ agent.duplicate() for i in range(num_particles-1) ]
    default_options = {'c1': 0.5, 'c2': 0.3, 'w':0.9}
    options = agent.parameters.get("options", default_options)
    for calibration_object in agent.model.adjustables:
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
        # NOTE: this partial chaining to move calibration_object requirements through the pipeline
        #causes some issues with multiplrocessing if the calibration_object (e.g. CalibrationSet)
        #contains non-pickleable components, which with the new plugin system it does if the plugins are loaded
        #from a module. Using class scoped/namespaced plugins and registering the class seems to avoid this problem
        cf = partial(cost_func, calibration_object, agents, _pool)
        # Perform optimization
        #For pyswarm, DO NOT use the embedded multi-processing -- it is impossible to track the mapping of an agent to the params
        cost, pos = optimizer.optimize(cf, iters=iterations, n_processes=None)
        calibration_object.df.loc[:,'global_best'] = pos
        calibration_object.check_point(iterations, agent.job)
        print(f"Best params with cost {cost}:")
        print(calibration_object.df[['param','global_best']].set_index('param'))
