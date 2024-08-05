from __future__ import annotations

import typing

import hydrotools.nwis_client
import pandas as pd
from ngen.cal import hookimpl

if typing.TYPE_CHECKING:
    from datetime import datetime


class UsgsObservations:
    CFS_TO_CSM = 0.028316847
    """ft**3/s to m**3/s"""

    def __init__(self):
        self._client = hydrotools.nwis_client.IVDataService()

    @hookimpl(trylast=True)
    def ngen_cal_model_observations(
        self,
        id: str,
        start_time: datetime,
        end_time: datetime,
        simulation_interval: pd.Timedelta,
    ) -> pd.Series:
        df = self._client.get(sites=id, startDT=start_time, endDT=end_time)

        df.set_index("value_time", inplace=True)
        ds = df["value"].resample(simulation_interval).nearest()
        ds.rename("obs_flow", inplace=True)

        # convert from CFS to CMS observations
        ds = ds * UsgsObservations.CFS_TO_CSM
        return ds
