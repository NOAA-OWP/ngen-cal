""" 
Test module for the grew wolf optimizer
"""
from ngen.cal.optimizers.grey_wolf import GlobalBestGWO as GreyWolfOptimizer
import numpy as np
np.random.seed(42)
from pathlib import Path
import pytest
import shutil

@pytest.fixture(scope="session")
def gwo_optimizer():
    n_particles = 4
    dims = 2
    bounds = ([0,0], [1,1])
    path = Path('./test_1')
    if( path.exists() ):
        shutil.rmtree(path)
    
    optimizer = GreyWolfOptimizer(n_particles, dims, bounds=bounds,start_iter=0,
                                 calib_path=path, basinid=9999)
    return optimizer

@pytest.fixture(scope="session")
def gwo_restart_optimizer(gwo_optimizer):
    n_particles = 4
    dims = 2
    bounds = ([0,0], [1,1])
    path = Path('./test_1')

    def cost_func(a):
        return np.array([0.5, 0.5, 0.5, 0.1])

    # Perform optimization
    cost, pos = gwo_optimizer.optimize(cost_func, iters=1, n_processes=None)
    optimizer = GreyWolfOptimizer(n_particles, dims, bounds=bounds,start_iter=1,
                                  calib_path=path, basinid=9999)
    return optimizer

def test_swarm_init(gwo_optimizer):
    assert gwo_optimizer

