# Monkey patch pydantic to allow schema serialization of PyObject types to string
from pydantic import PyObject
def pyobject_schema(cls, field_schema):
            field_schema['type'] = 'string'

PyObject.__modify_schema__ = classmethod(pyobject_schema)

from .configuration import General, Model
from .calibratable import Calibratable, Adjustable, Evaluatable
from .calibration_set import CalibrationSet, UniformCalibrationSet
from .meta import JobMeta

from . import metric_functions
from . import plot_functions
from . import plot_output
from . import gwo_global_best
from . import gwo_swarms

from .metric_functions import (
    treat_values,
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
    calculate_all_metrics,
)

from .plot_functions import (
    plot_streamflow,
    plot_streamflow_precipitation,
    scatterplot_streamflow,
    plot_output,
    scatterplot_objfun,
    trim_axs,
    scatterplot_var,
    scatterplot_objfun_metric,
    barplot_metric,
    plot_fdc_calib,
    plot_fdc_valid,
    plot_cost_hist,
)          

from .validation_run import run_valid_ctrl_best
