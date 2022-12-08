#!/usr/bin/env python
import pandas as pd # type: ignore
from hydrotools.metrics.metrics import *

weights = [0.4, 0.2, 0.4]

def nash_sutcliffe(observed, simulated):
    mean_observed = observed.mean()
    mean_simulated = simulated.mean()

    top = (observed - simulated).apply(lambda x: x*x).sum()
    bottom = (observed - mean_observed).apply(lambda x: x*x).sum()
    #TODO/FIXME what happens when bottom = 0!?!?!?!?!?
    if bottom == 0:
        return -float('inf')
    return (1 - top/bottom)

def normalized_nash_sutcliffe(observed, simulated):
    nse = nash_sutcliffe(observed, simulated)
    return 1/(2-nse)

def inverted_nnse(observed, simulated):
    nnse = normalized_nash_sutcliffe(observed, simulated)
    return 1 - nnse

def kge(observed, simulated):
    return 1 - kling_gupta_efficiency(observed, simulated)

def peak_error_single(observed, simulated):
    max_sim = simulated.max()
    max_obs = observed.max()
    err = (max_sim - max_obs)/max_obs
    return err

def volume_error(observed, simulated):
    total_volume = (simulated - observed).sum()
    normalized = total_volume/observed.sum()
    return normalized

def custom(observed, simulated):
    nnse = weights[0]*( 1 - normalized_nash_sutcliffe(observed, simulated) )
    peak = weights[1]*abs( peak_error_single(observed, simulated) )
    volume = weights[2]*abs( volume_error(observed, simulated) )
    return nnse + peak + volume
