from __future__ import annotations

import typing

import pandas as pd
from hypy.hydrolocation.nwis_location import NWISLocation

from ngen.cal import hookimpl

if typing.TYPE_CHECKING:
    from datetime import datetime

    from hypy.nexus import Nexus


class UsgsObservations:
    CFS_TO_CSM = 0.028316847
    """ft**3/s to m**3/s"""

    @hookimpl(trylast=True)
    def ngen_cal_model_observations(
        self,
        nexus: Nexus,
        start_time: datetime,
        end_time: datetime,
        simulation_interval: pd.Timedelta,
    ) -> pd.Series:
        # use the nwis location to get observation data
        location = nexus._hydro_location
        assert isinstance(location, NWISLocation), f"expected hypy.hydrolocation.NWISLocation instance, got {type(location)}. cannot retrieve observations"

        try:
            df = location.get_data(start=start_time, end=end_time)
        except BaseException as e:
            raise RuntimeError(f"failed to retrieve observations for usgs gage: {location.station_id}") from e

        df.set_index("value_time", inplace=True)
        ds = df["value"].resample(simulation_interval).nearest()
        ds.rename("obs_flow", inplace=True)

        # convert from CFS to CMS observations
        ds = ds * UsgsObservations.CFS_TO_CSM
        return ds
