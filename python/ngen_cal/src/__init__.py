# Monkey patch pydantic to allow schema serialization of PyObject types to string
from pydantic import PyObject
def pyobject_schema(cls, field_schema):
            field_schema['type'] = 'string'

PyObject.__modify_schema__ = classmethod(pyobject_schema)

from .configuration import General, Model
from .calibratable import Calibratable, Adjustable, Evaluatable
from .calibration_set import CalibrationSet, UniformCalibrationSet
from .meta import CalibrationMeta
from .plot import *
