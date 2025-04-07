"""
This module contains classes/functions to support swarm optimization.
It contains third party open source codes from pyswarms, including class  
GlobalBestGWO, class Swarms and function create_swarm.
Author modified these codes and added function write_hist_iter_file 
and read_hist_iter_file.

@author: Xia Feng

----------------------------------------------------------------------------

pyswarms complies with MIT License:

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

import abc
from collections import namedtuple
import logging

import os
import shutil
import time
from typing import Tuple

from attr import attrib, attrs
from attr.validators import instance_of
import numpy as np
import pandas as pd

from pyswarms.utils.reporter import Reporter
from pyswarms.backend import generate_swarm


class SwarmOptimizer(abc.ABC):
    def __init__(
        self,
        n_particles,
        dimensions,
        bounds=None,
        center=1.0,
        ftol=-np.inf,
        ftol_iter=1,
        init_pos=None,
        start_iter=0,
        calib_path='./',
        basinid=None,
    ):
        """Initialize the swarm

        Creates a Swarm class depending on the values initialized

        Attributes
        ----------
        n_particles : int
            number of particles in the swarm.
        dimensions : int
            number of dimensions in the space.
        bounds : tuple of numpy.ndarray, optional
            a tuple of size 2 where the first entry is the minimum bound
            while the second entry is the maximum bound. Each array must
        center : list, optional
            an array of size :code:`dimensions`
        ftol : float, optional
            relative error in objective_func(best_pos) acceptable for
            convergence. Default is :code:`-np.inf`.
        ftol_iter : int
            number of iterations over which the relative error in
            objective_func(best_pos) is acceptable for convergence.
            Default is :1
        """
        # Initialize primary swarm attributes
        self.n_particles = n_particles
        self.dimensions = dimensions
        self.bounds = bounds
        self.swarm_size = (n_particles, dimensions)
        self.center = center
        self.ftol = ftol
        self.start_iter = start_iter
        self.hist_path = os.path.join(calib_path, 'History_Iteration')
        os.makedirs(self.hist_path, exist_ok=True)
        self.cost_iter_file = os.path.join(self.hist_path, '{}_cost_iteration.csv'.format(basinid))
        self.pbest_cost_iter_file = os.path.join(self.hist_path, '{}_pbest_cost_iteration.csv'.format(basinid))
        self.pbest_pos_iter_file = os.path.join(self.hist_path, '{}_pbest_pos_iteration.csv'.format(basinid))
        self.leader_cost_iter_file = os.path.join(self.hist_path, '{}_leader_cost_iteration.csv'.format(basinid))
        self.pos_iter_file = os.path.join(self.hist_path, '{}_pos_iteration.csv'.format(basinid))
        self.leader_pos_iter_file = os.path.join(self.hist_path, '{}_leader_pos_iteration.csv'.format(basinid))

        try:
            assert ftol_iter > 0 and isinstance(ftol_iter, int)
        except AssertionError:
            raise AssertionError(
                "ftol_iter expects an integer value greater than 0"
            )

        self.ftol_iter = ftol_iter
        self.init_pos = init_pos
        # Initialize named tuple for populating the history list
        self.ToHistory = namedtuple(
            "ToHistory",
            [
                "best_cost",
                "pbest_cost",
                "mean_pbest_cost",
                "leader_cost",
                "mean_leader_cost",
                "position",
                "leader_position",
            ],
        )
        # Initialize resettable attributes
        self.reset()


    def _populate_history(self, hist):
        """Populate all history lists.

        The :code:`cost_history`, :code:`mean_pbest_history`, and
        :code:`neighborhood_best` is expected to have a shape of
        :code:`(iters,)`,on the other hand, the :code:`pos_history`
        and :code:`velocity_history` are expected to have a shape of
        :code:`(iters, n_particles, dimensions)`

        Parameters
        ----------
        hist : collections.namedtuple
            Must be of the same type as self.ToHistory
        """
        self.cost_history.append(hist.best_cost)
        self.pbest_history.append(hist.pbest_cost)
        self.mean_pbest_history.append(hist.mean_pbest_cost)
        self.leader_history.append(hist.leader_cost)
        self.mean_leader_history.append(hist.mean_leader_cost)
        self.pos_history.append(hist.position)
        self.leader_pos_history.append(hist.leader_position)


    def write_hist_iter_file(self, i: int) -> None: 
        """Write variables generated at each iteration.

        Parameters
        ----------
        i :  current iteration
        """
        df_cost = pd.DataFrame({'iteration': i, 'global_best': self.swarm.best_cost, 'mean_local_best': np.mean(self.swarm.pbest_cost),
                                'mean_leader_best': np.mean(self.swarm.leader_cost)}, index=[0])
        df_cost.to_csv(self.cost_iter_file, mode='a', index=False, header=not os.path.exists(self.cost_iter_file))

        pbest_cost = pd.DataFrame(self.swarm.pbest_cost, columns=['local_best'])
        pbest_cost['iteration'] = i 
        pbest_cost['agent'] = range(self.n_particles) 
        pbest_cost.to_csv(self.pbest_cost_iter_file, mode='a', index=False, header=not os.path.exists(self.pbest_cost_iter_file))

        leader_cost = pd.DataFrame(self.swarm.leader_cost, columns=['leader_best'])
        leader_cost['iteration'] = i 
        leader_cost['rank'] = range(1, 4)
        leader_cost.to_csv(self.leader_cost_iter_file, mode='a', index=False, header=not os.path.exists(self.leader_cost_iter_file))

        pos = pd.DataFrame(self.swarm.position)
        pos['iteration'] = i 
        pos['agent'] = range(self.n_particles) 
        pos.to_csv(self.pos_iter_file, mode='a', index=False, header=not os.path.exists(self.pos_iter_file))

        pbest_pos = pd.DataFrame(self.swarm.pbest_pos)
        pbest_pos['iteration'] = i 
        pbest_pos['agent'] = range(self.n_particles) 
        pbest_pos.to_csv(self.pbest_pos_iter_file, mode='a', index=False, header=not os.path.exists(self.pbest_pos_iter_file))

        leader_pos = pd.DataFrame(self.swarm.leader_pos)
        leader_pos['iteration'] = i 
        leader_pos['rank'] = range(1, 4)
        leader_pos.to_csv(self.leader_pos_iter_file, mode='a', index=False, header=not os.path.exists(self.leader_pos_iter_file))


    def read_hist_iter_file(self) -> Tuple: 
        """Read variables used in optimization and clean up files.

        Returns
        ----------
        history of variables and the current values 
        """
        iteration = self.start_iter 
        df_cost = pd.read_csv(self.cost_iter_file)
        shutil.copy(str(self.cost_iter_file), str(self.cost_iter_file) + '_before_restart_' + time.strftime('%Y%m%d_%H%M%S'))
        df_cost[df_cost['iteration'] < iteration].to_csv(self.cost_iter_file, index=False)

        best_cost = df_cost[['iteration', 'global_best']]
        best_cost = best_cost[best_cost['iteration'] < iteration]
        best = best_cost.iloc[-1]['global_best']
        best_cost = best_cost['global_best'].tolist() 

        mean_pbest_cost = df_cost[['iteration', 'mean_local_best']]
        mean_pbest_cost = mean_pbest_cost[mean_pbest_cost['iteration'] < iteration]
        mpbest_cost = mean_pbest_cost['mean_local_best'].tolist() 

        mean_leader_cost = df_cost[['iteration', 'mean_leader_best']]
        mean_leader_cost = mean_leader_cost[mean_leader_cost['iteration'] < iteration]
        mleader_cost = mean_leader_cost['mean_leader_best'].tolist() 

        pbest_cost = pd.read_csv(self.pbest_cost_iter_file)
        shutil.copy(str(self.pbest_cost_iter_file), str(self.pbest_cost_iter_file) + '_before_restart_' + time.strftime('%Y%m%d_%H%M%S'))
        pbest_cost = pbest_cost[pbest_cost['iteration'] < iteration]
        pbest_cost.to_csv(self.pbest_cost_iter_file, index=False)
        iter_range = pbest_cost['iteration'][~pbest_cost['iteration'].duplicated()].values.tolist()
        pbest_cost = [pbest_cost[pbest_cost['iteration']==i]['local_best'].tolist() for i in iter_range]
        pbest = pbest_cost[len(pbest_cost)-1] 

        leader_cost = pd.read_csv(self.leader_cost_iter_file)
        shutil.copy(str(self.leader_cost_iter_file), str(self.leader_cost_iter_file) + '_before_restart_' + time.strftime('%Y%m%d_%H%M%S'))
        leader_cost = leader_cost[leader_cost['iteration'] < iteration]
        leader_cost.to_csv(self.leader_cost_iter_file, index=False)
        leader_cost = [leader_cost[leader_cost['iteration']==i]['leader_best'].tolist() for i in iter_range]

        pos = pd.read_csv(self.pos_iter_file)
        shutil.copy(str(self.pos_iter_file), str(self.pos_iter_file) + '_before_restart_' + time.strftime('%Y%m%d_%H%M%S'))
        pos = pos[pos['iteration'] < iteration]
        pos.to_csv(self.pos_iter_file, index=False)
        pos = [np.array(pos[pos['iteration']==i].iloc[:,0:self.dimensions]) for i in iter_range]
        current_pos = pos[len(pos)-1] 

        pbest_pos = pd.read_csv(self.pbest_pos_iter_file)
        shutil.copy(str(self.pbest_pos_iter_file), str(self.pbest_pos_iter_file) + '_before_restart_' + time.strftime('%Y%m%d_%H%M%S'))
        pbest_pos = pbest_pos[pbest_pos['iteration'] < iteration]
        pbest_pos.to_csv(self.pbest_pos_iter_file, index=False)
        pbest_pos = [np.array(pbest_pos[pbest_pos['iteration']==i].iloc[:,0:self.dimensions]) for i in iter_range]
        current_pbest_pos = pbest_pos[len(pbest_pos)-1] 

        leader_pos = pd.read_csv(self.leader_pos_iter_file)
        shutil.copy(str(self.leader_pos_iter_file), str(self.leader_pos_iter_file) + '_before_restart_' + time.strftime('%Y%m%d_%H%M%S'))
        leader_pos = leader_pos[leader_pos['iteration'] < iteration]
        leader_pos.to_csv(self.leader_pos_iter_file, index=False)
        leader_pos = [np.array(leader_pos[leader_pos['iteration']==i].iloc[:,0:self.dimensions]) for i in iter_range]
        current_leader_pos = leader_pos[len(leader_pos)-1]

        return (best_cost, pbest_cost, mpbest_cost, leader_cost, mleader_cost, pos, leader_pos, best, pbest, current_pos, current_pbest_pos, current_leader_pos)


    def update_history(self, i):
        """Update history."""
        hist = self.ToHistory(
            best_cost=self.swarm.best_cost,
            pbest_cost=self.swarm.pbest_cost,
            mean_pbest_cost=np.mean(self.swarm.pbest_cost),
            leader_cost=self.swarm.leader_cost,
            mean_leader_cost=np.mean(self.swarm.leader_cost),
            position=self.swarm.position,
            leader_position=self.swarm.leader_pos,
        )
        self._populate_history(hist)
        self.write_hist_iter_file(i)


    @abc.abstractmethod
    def optimize(self, objective_func, iters, n_processes=None, **kwargs):
        """Optimize the swarm for a number of iterations

        Performs the optimization to evaluate the objective
        function :code:`objective_func` for a number of iterations
        :code:`iter.`

        Parameters
        ----------
        objective_func : function
            objective function to be evaluated
        iters : int
            number of iterations
        n_processes : int
            number of processes to use for parallel particle evaluation
            Default is None with no parallelization
        kwargs : dict
            arguments for objective function

        Raises
        ------
        NotImplementedError
            When this method is not implemented.
        """
        raise NotImplementedError("SwarmOptimizer::optimize()")


    def reset(self):
        """Reset the attributes of the optimizer

        All variables/atributes that will be re-initialized when this
        method is defined here. Note that this method
        can be called twice: (1) during initialization, and (2) when
        this is called from an instance.

        It is good practice to keep the number of resettable
        attributes at a minimum. This is to prevent spamming the same
        object instance with various swarm definitions.

        Normally, swarm definitions are as atomic as possible, where
        each type of swarm is contained in its own instance. Thus, the
        following attributes are the only ones recommended to be
        resettable:

        * Swarm position matrix (self.pos)
        * Best scores and positions (gbest_cost, gbest_pos, etc.)

        Otherwise, consider using positional arguments.
        """
        # Initialize history lists
        if self.start_iter == 0:
            self.cost_history = []
            self.pbest_history = []
            self.mean_pbest_history = []
            self.leader_history = []
            self.mean_leader_history = []
            self.pos_history = []
            self.leader_pos_history = []
        else:
            result = self.read_hist_iter_file()
            self.cost_history = result[0]
            self.pbest_history = result[1]
            self.mean_pbest_history = result[2]
            self.leader_history = result[3]
            self.mean_leader_history = result[4]
            self.pos_history = result[5]
            self.leader_pos_history = result[6]

        # Initialize the swarm
        self.swarm = create_swarm(
            n_particles=self.n_particles,
            dimensions=self.dimensions,
            bounds=self.bounds,
            center=self.center,
            init_pos=self.init_pos,
        )
        if self.start_iter != 0:
            self.swarm.best_cost = result[7] 
            self.swarm.pbest_cost = result[8] 
            self.swarm.position = result[9]
            self.swarm.pbest_pos = result[10] 
            self.swarm.leader_pos = result[11] 
            self.swarm.best_pos = result[11][0]


def create_swarm(
    n_particles,
    dimensions,
    bounds=None,
    center=1.0,
    init_pos=None,
):
    """Generate a Swarm class 

    Parameters
    ----------
    n_particles : int
        number of particles to be generated in the swarm.
    dimensions: int
        number of dimensions to be generated in the swarm
    bounds : tuple of np.ndarray or list
        a tuple of size 2 where the first entry is the minimum bound while
        the second entry is the maximum bound. Each array must be of shape
        :code:`(dimensions,)`. Default is `None`
    center : numpy.ndarray, optional
        a list of initial positions for generating the swarm. Default is `1`
    init_pos : numpy.ndarray, optional
        option to explicitly set the particles' initial positions. Set to
        :code:`None` if you wish to generate the particles randomly.

    Returns
    -------
    Swarm class
    """
    position = generate_swarm(
        n_particles,
        dimensions,
        bounds=bounds,
        center=center,
        init_pos=init_pos,
    )

    return Swarm(position)


@attrs
class Swarm(object):
    """A Swarm Class

    Attributes
    ----------
    position : numpy.ndarray
        position-matrix at a given timestep of shape :code:`(n_particles, dimensions)`
    n_particles : int
        number of particles in a swarm.
    dimensions : int
        number of dimensions in a swarm.
    pbest_pos : numpy.ndarray
        personal best positions of each particle of shape :code:`(n_particles, dimensions)`
        Default is `None`
    best_pos : numpy.ndarray
        best position found by the swarm of shape :code:`(dimensions, )` for
        the :obj:`pyswarms.backend.topology.Star` topology and
        :code:`(dimensions, particles)` for the other topologies
    pbest_cost : numpy.ndarray
        personal best costs of each particle of shape :code:`(n_particles, )`
    best_cost : float
        best cost found by the swarm, default is :obj:`numpy.inf`
    current_cost : numpy.ndarray
        the current cost found by the swarm of shape :code:`(n_particles, dimensions)`
    """
    # Required attributes
    position = attrib(type=np.ndarray, validator=instance_of(np.ndarray))
    # With defaults
    n_particles = attrib(type=int, validator=instance_of(int))
    dimensions = attrib(type=int, validator=instance_of(int))
    best_pos = attrib(
        type=np.ndarray,
        default=np.array([]),
        validator=instance_of(np.ndarray),
    )
    pbest_cost = attrib(
        type=np.ndarray,
        default=np.array([]),
        validator=instance_of(np.ndarray),
    )
    best_cost = attrib(
        type=float, default=np.inf, validator=instance_of((int, float))
    )
    current_cost = attrib(
        type=np.ndarray,
        default=np.array([]),
        validator=instance_of(np.ndarray),
    )
    pbest_pos = attrib(
        type=np.ndarray,
        default=np.array([]),
        validator=instance_of(np.ndarray),
    )
    leader_cost = attrib(
        type=np.ndarray,
        default=np.array([]),
        validator=instance_of(np.ndarray),
    )
    leader_pos = attrib(
        type=np.ndarray,
        default=np.array([]),
        validator=instance_of(np.ndarray),
    )
    @n_particles.default
    def n_particles_default(self):
        return self.position.shape[0]

    @dimensions.default
    def dimensions_default(self):
        return self.position.shape[1]
