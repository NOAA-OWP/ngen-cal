from collections import namedtuple, deque
import logging
import numpy as np
from pathlib import Path
import pandas as pd
import multiprocessing as mp
from pyswarms.base import SwarmOptimizer
from pyswarms.backend import Swarm, generate_swarm
from pyswarms.backend.topology import Star
from pyswarms.utils.reporter import Reporter
from pyswarms.backend.operators import compute_pbest, compute_objective_function

import shutil
import time
from typing import Tuple, List, Optional

def create_swarm(
    n_particles,
    dimensions,
    bounds=None,
    center=1.0,
    init_pos=None,
    options={}
):
    """Generate a Swarm class with no velocity

    The pyswarms backend uses a velocity component for general particle
    swarms.  The Grey Wolf doesn't use this, and needs to create
    a swarm with no velocity, so this function passes an empty array for velocities
    to the base Swarm.

    see :func:`pyswarms.backend.create_swarm` for argument descriptions
    """
    position = generate_swarm(
        n_particles,
        dimensions,
        bounds=bounds,
        center=center,
        init_pos=init_pos,
    )

    return Swarm(position, np.array([]), options=options)


class GreyWolfOptimizer(SwarmOptimizer):
    """_summary_

    Args:
        SwarmOptimizer (_type_): _description_
    """
    def __init__(self, *args, **kwargs):
        # Pop custom kwargs for this subclass
        self.start_iter: int = kwargs.pop("start_iter", 0)
        self.calib_path: Path = Path( kwargs.pop("calib_path", "./") )
        self.id = kwargs.pop("basinid", None)
        self.hist_path: Path = self.calib_path / 'History_Iteration'
        self.hist_path.mkdir(parents=True, exist_ok=True)
        # TODO consolidate these into single file?
        self.cost_iter_file: Path = self.hist_path / 'cost_iteration.csv'
        self.pbest_cost_iter_file: Path = self.hist_path / 'pbest_cost_iteration.csv'
        self.pbest_pos_iter_file: Path = self.hist_path /'{}_pbest_pos_iteration.csv'
        self.leader_cost_iter_file: Path = self.hist_path / '{}_leader_cost_iteration.csv'
        self.position_iter_file: Path = self.hist_path / '{}_pos_iteration.csv'
        self.leader_pos_iter_file: Path = self.hist_path / '{}_leader_pos_iteration.csv'
        #Initialize base class
        super(GreyWolfOptimizer, self).__init__(*args, **kwargs)
        self._cost_attrs = ["best_cost", "pbest_cost",
                            "mean_pbest_cost", "leader_cost",
                            "mean_leader_cost"]
        self._pos_attrs = ["position", "leader_position"]
        #Customize GWO history
        self.ToHistory = namedtuple(
            "ToHistory",
            self._cost_attrs + self._pos_attrs
        )
        #TODO set these in init?  or just let `reset()` handle it?
        # for a in self._pos_attrs:
        #     self.__setattr__( a + "_history", [] )
        # for a in self._cost_attrs:
        #     self.__setattr__( a.replace("_cost", "_history"), [] )
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

    def _hist_to_csv(self, i: int, name: str, index: List, key: str, label: Optional[str]=None) -> None:
        """Helper function to serialize history from class attribute

        Args:
            i (int): iteration to save
            name (str): attribute name containing history
            index (List): index values of the history list
            key (str): name of the index column in saved output
            label (Optional[str], optional): Column label of attribute. Defaults to None.
        """
        data = getattr(self.swarm, name)
        if(label):
            df = pd.DataFrame(data, columns=[label])
        else:
            df = pd.DataFrame(data)
        df['iteration'] = i 
        df[key] = index
        fname = getattr(self, name+"_iter_file")
        df.to_csv(fname, mode='a', index=False, header=not Path(fname).exists())

    def write_hist_iter_file(self, i: int) -> None: 
        """Write variables generated at each iteration.

        Parameters
        ----------
        i :  current iteration

        """
        df_cost = pd.DataFrame({'iteration': i, 'global_best': self.swarm.best_cost, 'mean_local_best': np.mean(self.swarm.pbest_cost),
                                'mean_leader_best': np.mean(self.swarm.leader_cost)}, index=[0])
        df_cost.to_csv(self.cost_iter_file, mode='a', index=False, header=not Path(self.cost_iter_file).exists())
        particle_index = range(self.n_particles)
        gw_index = range(1,4)
        self._hist_to_csv(i, 'pbest_cost', particle_index, 'agent', label='local_best')
        self._hist_to_csv(i, 'position', particle_index, 'agent')
        self._hist_to_csv(i, 'pbest_pos', particle_index, 'agent')
        self._hist_to_csv(i, 'leader_cost', gw_index, 'rank', label='leader_best')
        self._hist_to_csv(i, 'leader_pos', gw_index, 'rank')

    def _get_best_from_df(self, df: pd.DataFrame, name: str, iter_range: Optional[List]=None) -> Tuple[float, List[float]]:
        """Provide the history and best cost from the given dataframe

        Args:
            df (DataFrame): dataframe containing swarm history or cost
            name (str): history or attribute variable to extract
            iter_range (Optional[List], optional): If provided, only extract
                hitory data and the best, otherwise extract cost for current iteration.
                Defaults to None.

        Returns:
            Tuple[float, List[float]]: best value and history list it was extracted from
        """
        if( iter_range ):
            hist = [df[df['iteration']==i][name].tolist() for i in iter_range]
            best = hist[len(hist)-1] 
        else:
            cost = df[['iteration', name]]
            cost = cost[cost['iteration'] == self.start_iter]
            best = cost.iloc[-1][name]
            hist = cost[name].tolist()
        
        return best, hist
 
    def _get_pos_from_df(self, df: pd.DataFrame, iter_range: List) -> Tuple[int, List]:
        """Get list of positions and current position from given dataframe

        Args:
            df (DataFrame): dataframe with `iteration` key
            iter_range (List): range to extract positions for

        Returns:
            Tuple[int, List]: the current position as a scalar,
                              and the complete list of positions.
        """

        pos = [np.array(df[df['iteration']==i].iloc[:,0:self.dimensions]) for i in iter_range]
        current_pos = pos[len(pos)-1] 
        return current_pos, pos

    def _get_and_dup_df(self, fname: Path) -> pd.DataFrame:
        """
        Read csv data into dataframe and make a copy of the
            old data frame as (fname + _before_restart _ timestamp).csv
        
        Args:
            fname (Path): csv file to read and duplicate

        Returns:
            pd.DataFrame: data from csv at self.start_iter
        """
        df = pd.read_csv(fname)
        shutil.copy(str(fname), str(fname) + '_before_restart_' + time.strftime('%Y%m%d_%H%M%S'))
        df = df[df['iteration'] == self.start_iter]
        df.to_csv(fname, index=False)
        return df

    def read_hist_iter_file(self) -> Tuple: 
        """Read variables used in optimization and clean up files.

        Returns
        ----------
        history of variables and the current values 

        """
        df_cost = self._get_and_dup_df(self.cost_iter_file)
        self.swarm.best_cost, self.cost_history = self._get_best_from_df(df_cost, 'global_best')
        _, self.mean_pbest_history = self._get_best_from_df(df_cost, 'mean_local_best')
        _, self.mean_leader_history = self._get_best_from_df(df_cost, 'mean_leader_best')

        pbest_cost = self._get_and_dup_df(self.pbest_cost_iter_file)
        iter_range = pbest_cost['iteration'][~pbest_cost['iteration'].duplicated()].values.tolist()
        self.swarm.pbest_cost, self.pbest_history = self._get_best_from_df(pbest_cost, 'local_best', iter_range)
        
        leader_cost = self._get_and_dup_df(self.leader_cost_iter_file)
        _, self.leader_history = self._get_best_from_df(leader_cost, 'leader_best', iter_range)

        pos = self._get_and_dup_df(self.position_iter_file)
        self.swarm.position, self.pos_history = self._get_pos_from_df(pos, iter_range)

        pbest_pos = self._get_and_dup_df(self.pbest_pos_iter_file)
        self.swarm.pbest_pos, _ = self._get_pos_from_df(pbest_pos, iter_range)

        leader_pos = self._get_and_dup_df(self.leader_pos_iter_file)
        self.swarm.leader_pos, self.leader_pos_history = self._get_pos_from_df(leader_pos, iter_range)
        self.swarm.best_pos = self.swarm.leader_pos[0]

    def update_history(self, i):
        """Update history."""
        _hist={ a: getattr(self.swarm, a, None) for a in self._cost_attrs+self._pos_attrs}
        _hist['mean_pbest_cost'] = np.mean(self.swarm.pbest_cost)
        _hist['mean_leader_cost'] = np.mean(self.swarm.leader_cost)
        hist = self.ToHistory(**_hist)
        self._populate_history(hist)
        self.write_hist_iter_file(i)
    
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

    def reset(self):
        """Reset the attributes of the optimizer

        From the pyswarms documentation:
        This function can be called twice:
            (1) during initialization, and 
            (2) when this is called from an instance.

        Initialize history and swarm attributes, when
        self.start_iter is not 0, history and attriutes
        are set using @read_hist_iter_file()

        """
        # Initialize the swarm
        # Do this before potentially updating
        # swarm states from restart
        self.swarm = create_swarm(
            n_particles=self.n_particles,
            dimensions=self.dimensions,
            bounds=self.bounds,
            center=self.center,
            init_pos=self.init_pos,
        )
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
            self.read_hist_iter_file()

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
