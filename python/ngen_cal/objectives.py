#!/usr/bin/env python
import pandas as pd # type: ignore

weights = [0.4, 0.2, 0.4]

def nash_sutcliffe(simulated, observed):
    mean_observed = observed.mean()
    mean_simulated = simulated.mean()

    top = (observed - simulated).apply(lambda x: x*x).sum()
    bottom = (observed - mean_observed).apply(lambda x: x*x).sum()
    #TODO/FIXME what happens when bottom = 0!?!?!?!?!?
    if bottom == 0:
        return -float('inf')
    return (1 - top/bottom)

def normalized_nash_sutcliffe(simulated, observed):
    nse = nash_sutcliffe(simulated, observed)
    return 1/(2-nse)

def peak_error_single(simulated, observed):
    max_sim = simulated.max()
    max_obs = observed.max()
    err = (max_sim - max_obs)/max_obs
    return err

def volume_error(simulated, observed):
    total_volume = (simulated - observed).sum()
    normalized = total_volume/observed.sum()
    return normalized

def custom(simulated, observed):
    nnse = weights[0]*( 1 - normalized_nash_sutcliffe(simulated, observed) )
    peak = weights[1]*abs( peak_error_single(simulated, observed) )
    volume = weights[2]*abs( volume_error(simulated, observed) )

    return nnse + peak + volume
