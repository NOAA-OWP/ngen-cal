"""
This module contains functions to process model output and compute statistical measures.
@author: Xia Feng
"""

import math
from typing import Union, Optional, Dict
import warnings

import numpy as np
import pandas as pd
import scipy.stats as sp
from scipy.stats import pearsonr

from hydrotools.metrics import metrics as hm

__all__ = ['treat_values',
           'pearson_corr',
           'mean_abs_error',
           'root_mean_squared_error',
           'rmse_std_ratio',
           'percent_bias',
           'NSE',
           'Weighted_NSE',
           'KGE',
           'categorical_score',
           'pbias_fdc',
          ]


def treat_values(
    df: pd.DataFrame, 
    remove_neg: Optional[bool] = False, 
    remove_na: Optional[bool] = False, 
    replace_zero: Optional[bool] = False,
) -> pd.DataFrame:
    """Remove NaN, inf and negative values, and replace zero values of time series.

    Parameters
    ----------
    df : Contains time series of observation and simulation
    remove_neg : If True, when negative value occurs at the ith element of observation or simulation
        the ith element of both observation or simulation is removed.
    remove_nan : If True, when NaN value occurs at the ith element of observation or simulation, 
        the ith element of both observation or simulation is removed.
    replace_zero : If True, when the zero value occurs at the ith element of observation or simulation, 
        all observation and simulation are added with 1/100 of mean of observation according to Pushpalatha et al (2012).

    Returns
    -------
    df : Ouput DataFrame 

    References
    ----------
    Pushpalatha, R., C. Perrin, N. L. Moine, V. Andreassian, 2012: A review of efficiency criteria suitable for evaluating low-flow simulations.
        Journal of Hydrology, 420-421, 171-182.

    """

    df = df.copy()
    colnames = list(df.columns)

    # Remove rows with duplicated datetime
    df.drop_duplicates(subset=colnames[0], inplace=True)
    df.sort_values(by=colnames[0], na_position='last')

    # Remove rows with missing values
    if remove_na:
        na_index = df.isin([np.nan, np.inf, -np.inf])
        df = df[~na_index]
        df.dropna(inplace=True)

    # Remove rows with negative values
    if remove_neg:
        if (df[colnames[1:]]<0).all(axis=1).any():
            df = df[~(df[colnames[1:]]<0).all(axis=1)]

    # Replace zero values
    if replace_zero:
        if df[colnames[1:]].min().values.min() == 0:
            df[colnames[1:]] = df[colnames[1:]] + 1.0/100.0*df[colnames[1]].mean()

    return df


def pearson_corr(
    y_true: pd.Series,
    y_pred: pd.Series,
) -> float:
    """Compute mean squared error, or optionally root mean squared error.

    Parameters
    ----------
    y_true : Ground truth or observations
    y_pred : Modeled values or simulations

    Returns
    -------
    corr : float
    p_value : float

    """

    # Compute
    corr, p_value = pearsonr(y_pred, y_true)

    return corr, p_value


def mean_abs_error(
    y_true: pd.Series,
    y_pred: pd.Series,
) -> float:
    """Compute mean absolute error between simulation and observation.

    Parameters
    y_true : Ground truth or observations
    y_pred : Modeled values or simulations

    Returns
    -------
    Mean absolute error

    """

    return np.sum(np.absolute(np.subtract(y_pred, y_true)))/len(y_true)


def root_mean_squared_error(
    y_true: pd.Series,
    y_pred: pd.Series,
    root: Optional[bool] = True,
) -> float:
    """Compute root mean squared error, or optionally mean squared error.

    Parameters
    ----------
    y_true : Ground truth or observations
    y_pred : Modeled values or simulations
    root :  When False, return the mean squared error.

    Returns
    -------
    Root mean squared error or mean squared error

    """

    # Compute mean squared error
    MSE = np.sum(np.subtract(y_true, y_pred) ** 2.0) / len(y_true)

    # Return RMSE, optionally return mean squared error
    if not root:
        return MSE
    return np.sqrt(MSE)


def rmse_std_ratio(
    y_true: pd.Series,
    y_pred: pd.Series,
    root: Optional[bool] = False,
) -> float:
    """Compute ratio of RMSE between simulation and observation to standard deviation of observation.

    Parameters
    ----------
    y_true : Ground truth or observations
    y_pred : Modeled values or simulations

    Returns
    -------
    rsr: ratio of RMSE and standard deviation of observation

    """

    rmse = root_mean_squared_error(y_true, y_pred, root=True)
    denominator = np.std(y_true)

    if denominator != 0:
        rsr = rmse/denominator
    else:
        rsr = np.nan
        warnings.warn("'np.std(y_true) = 0', can't compute RSR")

    return rsr


def percent_bias(
    y_true: pd.Series,
    y_pred: pd.Series,
) -> float:
    """Compute mean squared error, or optionally root mean squared error.

    Parameters
    ----------
    y_true : Ground truth or observations
    y_pred : Modeled values or simulations

    Returns
    -------
    pbias : float

    """

    # compute
    denominator = np.sum(y_true)
    pbias = np.sum(np.subtract(y_pred, y_true))/denominator * 100

    if (denominator != 0):
        return pbias
    else:
        return np.nan
        warnings.warn("'np.sum(y_true) = 0', can't compute PBIAS")


def NSE(
    y_true: pd.Series,
    y_pred: pd.Series,
    fun: Optional[str] = None,
    epsilon: Union[None, str] = [None, "Pushpalatha2012"],
    normalized: Optional[bool] = False,
) -> float:
    """Compute Nash-Sutcliffe efficiency.

    Parameters
    ----------
    y_true : Ground truth or observations
    y_pred : Modeled values or simulations
    fun: Transformation function applied to y_true and y_pred
    epsilon: Value added to both y_true and y_pred if fun is logarithm or other functions
        that are mathematically impossible to compute transformation of zero flows:
        1) 0: zero value
        2) "Pushpalatha2012": 1/100 of mean of y_true
        3) other numeric value
    normalized : If True, convert Nash-Sutcliffe efficiency to the normalized value.

    Returns
    ----------
    Nash-Sutcliffe Efficiency value

    """

    # Transform values
    if fun == 'log':
        if epsilon=='Pushpalatha2012':
            y_true = y_true + np.mean(y_true)/100
            y_pred = y_pred + np.mean(y_true)/100
            if y_true.min() == 0.0: # if not np.all(y_true)
                y_true = y_true + 0.01
            if y_pred.min() == 0.0:
                y_pred = y_pred + 0.01
        y_true = np.log(y_true)
        y_pred = np.log(y_pred)

    # Compute components
    numerator = np.sum(np.subtract(y_pred, y_true) ** 2.0) / len(y_true)
    denominator = np.sum(np.subtract(y_true, np.mean(y_true)) ** 2.0) / len(y_true)

    # Compute score, optionally normalize
    if (denominator != 0):
        if normalized:
            return 1.0 / (1.0 + numerator/denominator)
        return 1.0 - numerator/denominator
    else:
        return np.nan
        warnings.warn("'denominator = 0', can't compute NSE")


def Weighted_NSE(
    y_true: pd.Series,
    y_pred: pd.Series,
    weight: Optional[float] = 0.5,
    normalized: Optional[bool] = False,
) -> float:
    """ Compute weighted average of Nash-Sutcliffe efficiency of raw time series and 
    Nash-Sutcliffe efficiency of logrithmic time series.

    Parameters
    ----------
    y_true : Ground truth or observations
    y_pred : Modeled values or simulations
    weight : weight value for Nash-Sutcliffe efficiency component
    normalized : Whether to convert the weighted Nash-Sutcliffe efficiency to the normalized valu

    Returns
    ----------
    Weighted Nash-Sutcliffe Efficiency value

    """

    # Compute NSE
    nse = NSE(y_true, y_pred)

    # Compute NSELog
    nselog = NSE(y_true, y_pred, fun="log", epsilon='Pushpalatha2012')

    # Compute weighted NSE
    nsewt = nse*weight + nse*(1-weight)

    if normalized:
       return 1.0 / (2.0 - nsewt)
    return nsewt


def KGE(
    y_true: pd.Series,
    y_pred: pd.Series,
    r_scale: Optional[float] = 1.0,
    a_scale: Optional[float] = 1.0,
    b_scale: Optional[float] = 1.0,
) -> float:
    """Compute Kling-Gupta efficiency between simulation and observation.

    Parameters
    ----------
    y_true : Ground truth or observations
    y_pred : Modeled values or simulations
    r_scale : correlation scaling factor
    a_scale : relative variability scaling factor
    b_scale : relative mean scaling factor

    Returns
    ----------
    Kling-Gupta efficiency value

    References
    ----------
    Gupta, H. V., Kling, H., Yilmaz, K. K., & Martinez, G. F. (2009). Decomposition of the mean
        squared error and NSE performance criteria: Implications for improving hydrological modelling.
        Journal of hydrology, 377(1-2), 80-91.

    """

    return hm.kling_gupta_efficiency(y_true, y_pred, r_scale, a_scale, b_scale)


def pbias_fdc(
    y_true: pd.Series,
    y_pred: pd.Series,
    bqthr: Optional[float] = 0.9,
    lqthr: Optional[float] = 0.7,
    hqthr: Optional[float] = 0.2,
    pqthr: Optional[float] = 0.1,
    warning_msg: Optional[bool] = False,
) -> Dict[str, float]:
    """Compute percent bias of flow duration curve (FDC) high-segment volume,
    midsegment slope and low-segment volume according to Yilmaz et al (2008).

    Parameters
    ----------
    y_true : Ground truth or observations
    y_pred : Modeled values or simulations 
    bqthr : baseflow exceedance probability 
    lqthr : low flow exceedance probability
    hqthr : high flow exceedance probability
    pqthr : peak flow exceedance probability 
    warning_msg : If True, print warining messages. 

    Returns
    -------
    Dictionary of pbias of peak flow, slope and low flow of FDC

    References
    ----------
    Yilmaz, K. K., H. V. Gupta, and T. Wagener (2008), A process-based diagnostic approach to
        modelevaluation: Application to the NWS distributed hydrologic model,
        Water Resource Research, 44, W09417,doi:10.1029/2007WR006716.

    """

    # Sort and rank
    y_true_sort = np.sort(y_true, axis=0)[::-1]
    y_pred_sort = np.sort(y_pred, axis=0)[::-1]

    # Compute exceedence probabilities
    y_true_prob = np.arange(1, len(y_true) + 1) / len(y_true)
    y_pred_prob = np.arange(1, len(y_pred) + 1) / len(y_pred)

    # Compute pbias of peak flow segment of FDC (require same number of elements)
    numerator = np.sum(np.subtract(y_pred_sort[y_pred_prob<pqthr], y_true_sort[y_true_prob<pqthr]))
    denominator = np.sum(y_true_sort[y_true_prob<pqthr])
    if denominator != 0:
        pbias_hseg_fdc = numerator/denominator * 100
    else:
        pbias_hseg_fdc = np.nan
        if warning_msg:
            warnings.warn("'denominator = 0', can't compute PBIAS for peak flow of FDC")

    # Compute pbias of midsegment slope of FDC 
    term1 = y_pred_sort[np.abs(y_pred_prob-hqthr).argmin()]
    term2 = y_pred_sort[np.abs(y_pred_prob-lqthr).argmin()]
    if (term1 != 0 and term2 != 0):
        pred_term = np.log(term1) - np.log(term2)
        denominator = np.log(y_true_sort[np.abs(y_true_prob-hqthr).argmin()]) - np.log(y_true_sort[np.abs(y_true_prob-lqthr).argmin()])
        numerator = pred_term - denominator
        if denominator > 0:
            pbias_mseg_fdc = numerator/denominator * 100
        else:
            pbias_mseg_fdc = np.nan
            if warning_msg:
                warnings.warn("'denominator = 0', can't compute PBIAS for slope of FDC")
    else:
        pbias_mseg_fdc = np.nan
        if warning_msg:
            warnings.warn("'0 as argument for np.log', can't compute PBIAS for slope of FDC")

    # Compute pbias of low flow segment of FDC
    term1 = (y_pred_sort[y_pred_prob>bqthr]).min()
    term2 = y_pred_sort.min()
    term3 = (y_true_sort[y_true_prob>bqthr]).min()
    term4 = y_true_sort.min()
    if (all([term1 != 0, term2 != 0, term3 != 0, term4 != 0])):
        denominator = np.sum(np.log(y_true_sort[y_true_prob>bqthr]) - np.log(y_true_sort.min()))
        numerator = np.sum(np.log(y_pred_sort[y_pred_prob>bqthr]) - np.log(y_pred_sort.min())) - denominator
        if denominator != 0:
            pbias_lseg_fdc = numerator/denominator * (-100)
        else:
            pbias_lseg_fdc = np.nan
            if warning_msg:
                warnings.warn("'denominator = 0', can't compute PBIAS for low flow of FDC")
    else:
        pbias_lseg_fdc = np.nan
        if warning_msg:
            warnings.warn("'0 as argument for np.log', can't compute PBIAS for low flow of FDC")

    return {"HSEG_FDC": pbias_hseg_fdc, "MSEG_FDC": pbias_mseg_fdc, "LSEG_FDC": pbias_lseg_fdc}


def categorical_score(
    y_true: pd.Series,
    y_pred: pd.Series,
    threshold: float,
) -> Dict[str, float]:
    """Compute probability of detection (POD), probability of false_alarm (FAR), 
    cirtical success index (CSI) and frequency bias (FBIAS).

    Parameters
    ----------
    y_true : Ground truth or observations
    y_pred : Modeled values or simulations
    threshold : threshold value

    Returns
    -------
    Dictionary of  categorical score values

    """

    observed = y_true>threshold
    simulated = y_pred>threshold
    contingency_table = hm.compute_contingency_table(observed, simulated)
    pod = hm.probability_of_detection(contingency_table)
    far = hm.probability_of_false_alarm(contingency_table)
    csi = hm.threat_score(contingency_table)
    fbias = hm.frequency_bias(contingency_table)

    return {'POD':pod, 'FAR':far, 'CSI':csi, 'FBIAS':fbias}


_all_metrics = [
    pearson_corr,
    mean_abs_error,
    root_mean_squared_error,
    rmse_std_ratio,
    percent_bias,
    NSE,
    Weighted_NSE,
    KGE,
    categorical_score,
    pbias_fdc,
]


def calculate_all_metrics(
    y_true: pd.Series, 
    y_pred: pd.Series, 
    threshold: Optional[float] = None,
) -> Dict[str, float]:
    """Compute All Statistical Metrics between simulation and observation.

    Parameters
    ----------
    y_true : Ground truth or observations
    y_pred : Modeled values or simulations 
    threshold : threshold value for calculating categorical scores

    Returns
    ----------
    result : dictionary of metric values

    """

    metric_name = {"pearson_corr": "Corr", "mean_abs_error": "MAE", "root_mean_squared_error": "RMSE", "rmse_std_ratio": "RSR",
                   "percent_bias": "PBIAS", "Weighted_NSE": "NSEWt", "KGE": "KGE"}
    result = {}
    for f in _all_metrics:
        if f.__name__ == "pearson_corr":
             result.update({metric_name[f.__name__]: f(y_true, y_pred)[0]})
        elif f.__name__ == "NSE":
             result.update({f.__name__: f(y_true, y_pred)})
             result.update({"NSELog": f(y_true, y_pred, fun = "log", epsilon = "Pushpalatha2012")})
        elif f.__name__ == "categorical_score":
             if threshold:
                 result.update(f(y_true, y_pred, threshold))
             else:
                 result.update({'POD': np.nan, 'FAR': np.nan, 'CSI': np.nan, 'FBIAS': np.nan})
        elif f.__name__ == "pbias_fdc":
             result.update(f(y_true, y_pred))
        else:
             result.update({metric_name[f.__name__]: f(y_true, y_pred)})
    return result
