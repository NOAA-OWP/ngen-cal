"""
This module performs parameter calibration using grey wolf optimization.  
It contains third party open source codes, class GlobalBestGWO from pyswarms
and class gwo from SwarmPackagePy. Author made further modifications.

@author: Xia Feng

----------------------------------------------------------------------------

pyswarms complies with MIT License as follows:

Copyright (c) 2017, Lester James V. Miranda

Permission is hereby granted, free of charge, to any person obtaining 
a copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the Software
is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in 
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A   
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT  
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION 
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE 
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""

import logging
from collections import deque
import multiprocessing as mp

import numpy as np

from pyswarms.backend.operators import compute_pbest, compute_objective_function
from pyswarms.backend.topology import Star
from pyswarms.utils.reporter import Reporter

from .gwo_swarms import SwarmOptimizer


class GlobalBestGWO(SwarmOptimizer):
    def __init__(
        self,
        n_particles,
        dimensions,
        bounds=None,
        center=1.00,
        ftol=-np.inf,
        ftol_iter=1,
        init_pos=None,
        start_iter=0,
        calib_path='./',
        basinid=None,
    ):
        """Initialize the swarm

        Attributes
        ----------
        n_particles : int
            number of particles in the swarm.
        dimensions : int
            number of dimensions in the space.
        bounds : tuple of numpy.ndarray, optional
            a tuple of size 2 where the first entry is the minimum bound while
            the second entry is the maximum bound. Each array must be of shape
            :code:`(dimensions,)`.
        bh_strategy : str
            a strategy for the handling of out-of-bounds particles.
        center : list (default is :code:`None`)
            an array of size :code:`dimensions`
        ftol : float
            relative error in objective_func(best_pos) acceptable for
            convergence. Default is :code:`-np.inf`
        ftol_iter : int
            number of iterations over which the relative error in
            objective_func(best_pos) is acceptable for convergence.
            Default is :code:`1`
        init_pos : numpy.ndarray, optional
            option to explicitly set the particles' initial positions. Set to
            :code:`None` if you wish to generate the particles randomly.
        """
        super(GlobalBestGWO, self).__init__(
            n_particles=n_particles,
            dimensions=dimensions,
            bounds=bounds,
            center=center,
            ftol=ftol,
            ftol_iter=ftol_iter,
            init_pos=init_pos,
            start_iter=start_iter,
            calib_path=calib_path,
            basinid=basinid,
        )

        # Initialize logger
        self.rep = Reporter(logger=logging.getLogger(__name__))
        # Initialize the resettable attributes
        self.reset()
        # Initialize the topology
        self.top = Star()
        self.name = __name__

    def optimize(
        self, objective_func, iters, n_processes=None, verbose=True, **kwargs
    ):
        """Optimize the swarm for a number of iterations

        Performs the optimization to evaluate the objective
        function :code:`f` for a number of iterations :code:`iter.`

        Parameters
        ----------
        objective_func : callable
            objective function to be evaluated
        iters : int
            number of iterations
        n_processes : int
            number of processes to use for parallel particle evaluation (default: None = no parallelization)
        verbose : bool
            enable or disable the logs and progress bar (default: True = enable logs)
        kwargs : dict
            arguments for the objective function

        Returns
        -------
        tuple
            the global best cost and the global best position.
        """
        # Apply verbosity
        if self.start_iter>0:
            verbose = False 
        if verbose:
            log_level = logging.INFO
        else:
            log_level = logging.NOTSET

        self.rep.log("Obj. func. args: {}".format(kwargs), lvl=logging.DEBUG)
        self.rep.log(
            "Optimize for {} iters with {} particles and {} dimensions".format(iters, self.n_particles, self.dimensions),
            lvl=log_level,
        )

        # Setup Pool of processes for parallel evaluation
        pool = None if n_processes is None else mp.Pool(n_processes)

        ftol_history = deque(maxlen=self.ftol_iter)

        # Compute cost of initial swarm  
        if self.start_iter == 0:
            print("Compute cost of the initial swarm at iteration 1")
            self.swarm.current_cost = compute_objective_function(self.swarm, objective_func, pool=pool, **kwargs)
            self.swarm.pbest_cost = self.swarm.current_cost 
            self.swarm.pbest_pos = self.swarm.position
            alpha, beta, delta = self.__get_abd(self.swarm.n_particles, self.swarm.current_cost)
            self.update_history(1)
            initial_iter = self.start_iter
        else:
            print("Restart at iteration", self.start_iter)
            alpha, beta, delta = self.swarm.leader_pos[0], self.swarm.leader_pos[1], self.swarm.leader_pos[2]
            initial_iter = self.start_iter - 2

        for i in self.rep.pbar(iters, self.name) if verbose else range(initial_iter, iters):
            a = 2 - 2 * i / iters
            # Random parameters for alpha wolf
            r1 = np.random.random((self.n_particles, self.dimensions))
            r2 = np.random.random((self.n_particles, self.dimensions))
            A1 = 2 * r1 * a - a
            C1 = 2 * r2
            # Random parameters for beta wolf
            r1 = np.random.random((self.n_particles, self.dimensions))
            r1 = np.random.random((self.n_particles, self.dimensions))
            r2 = np.random.random((self.n_particles, self.dimensions))
            A2 = 2 * r1 * a - a
            C2 = 2 * r2
            # Random parameters for delta wolf
            r1 = np.random.random((self.n_particles, self.dimensions))
            r2 = np.random.random((self.n_particles, self.dimensions))
            A3 = 2 * r1 * a - a
            C3 = 2 * r2
            # Distance between candidate wolves and leading wolves
            Dalpha = abs(C1 * alpha - self.swarm.position)
            Dbeta = abs(C2 * beta - self.swarm.position)
            Ddelta = abs(C3 * delta - self.swarm.position)
            # Update position of candidate wolves 
            X1 = alpha - A1 * Dalpha
            X2 = beta - A2 * Dbeta
            X3 = delta - A3 * Ddelta
            self.swarm.position = (X1 + X2 + X3) / 3
            self.swarm.position = np.clip(self.swarm.position, self.bounds[0], self.bounds[1])
            # Compute current cost and update local best
            self.swarm.current_cost = compute_objective_function(self.swarm, objective_func, pool=pool, **kwargs)
            self.swarm.pbest_pos, self.swarm.pbest_cost = compute_pbest(self.swarm)
            # Update leader and best cost and the corresponding positions 
            alpha, beta, delta = self.__get_abd(self.swarm.n_particles, self.swarm.current_cost)
            # Compute best cost and position
            if verbose:
                self.rep.hook(best_cost=self.swarm.best_cost)
            # save history
            self.update_history(i+2)

        # Obtain the final best_cost and the final best_position
        final_best_cost = self.swarm.best_cost.copy()
        final_best_pos = self.swarm.best_pos.copy()
        # Write report in log and return final cost and position
        self.rep.log("Optimization finished | best cost: {}, best pos: {}".format(final_best_cost, final_best_pos), lvl=log_level) 
        # Close Pool of Processes
        if n_processes is not None:
            pool.close()
        return (final_best_cost, final_best_pos)

    def __get_abd(self, n, fitness):
        result = []
        fitness = [(fitness[i], i) for i in range(n)]
        fitness.sort()
        for i in range(3):
            result.append(self.swarm.position[fitness[i][1]])

        self.swarm.leader_pos = np.array(result) 
        self.swarm.leader_cost = [fitness[i][0] for i in range(3)]  

        if self.swarm.leader_cost[0] < self.swarm.best_cost:
            self.swarm.best_cost = self.swarm.leader_cost[0] 
            self.swarm.best_pos = self.swarm.leader_pos[0] 

        return result
