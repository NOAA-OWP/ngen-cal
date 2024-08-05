from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
from ngen.cal import hookimpl
from pandas import DataFrame, Series

if TYPE_CHECKING:
    from ngen.cal.meta import JobMeta

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ngen.cal.meta import JobMeta

class TrouteOutput:

    def __init__(self, filepath: Path) -> None:
        self._output_file = filepath

    def _get_dataframe(self) -> DataFrame | None:
        """Get the t-route output raw dataframe from either csv or hdf5 files

        Returns:
            DataFrame: _description_
        """
        if not self._output_file.exists():
            return None

        if self._output_file.suffix == '.csv':
            df = pd.read_csv(self._output_file)
            # 't0' is reference time
            df["t0"] = pd.to_datetime(df["t0"])
            # 'time' is the forecast hour
            df["time"] = pd.to_timedelta(df["time"])
            df["value_time"] = df["t0"] + df["time"]
            df.rename(columns={"flow": "value", df.columns[0]: "waterbody_code"}, inplace=True)
            df["waterbody_code"] = df["waterbody_code"].map(lambda x: f"wb-{x}")
            df.set_index("value_time", inplace=True)
        elif self._output_file.suffix == '.hdf5':
            # TODO: fix this
            df = pd.read_hdf(self._output_file)
            df.index = df.index.map(lambda x: 'wb-'+str(x))
            df.columns = pd.MultiIndex.from_tuples(df.columns)
        else:
            df = None
        return df

    # Try external provided output hooks, if those fail, try this one
    # this will only execute if all other hooks return None (or they don't exist)
    @hookimpl(specname="ngen_cal_model_output", trylast=True)
    def get_output(self, id: str) -> Series:
        #look for routed data
        #read the routed flow at the given id
        df = self._get_dataframe()
        if df is None:
            print("{} not found. Current working directory is {}".format(self._output_file, Path.cwd()))
            print("Setting output to None")
            # TODO: should never return None here.
            # revist why this is done this way and other ways to handle this.
            return None

        assert id in df["waterbody_code"].values, f"no simulated values found for waterbody {id}"
        ds = df.loc[df["waterbody_code"] == id, "value"]
        ds.name = "sim_flow"
        return ds
        # dt_range = pd.date_range(tnx_df.index[0], tnx_df.index[-1], len(output.index)).round('min')
        # output.index = dt_range

        #this may not be strictly nessicary...I think the _evalutate will align these...
        # output = output.resample('1h').first()
        # return output
        # output.name="sim_flow"

class NgenSaveOutput():

    runoff_pattern = "cat-*.csv"
    lateral_pattern = "nex-*.csv"
    terminal_pattern = "tnx-*.csv"
    coastal_pattern = "cnx-*.csv"
    routing_output = "flowveldepth_Ngen.csv"
    @hookimpl(trylast=True)
    def ngen_cal_model_iteration_finish(self, iteration: int, info: JobMeta) -> None:
        """
            After each iteration, copy the old outputs for possible future
            evaluation and inspection.
        """
        path = info.workdir
        out_dir = path/f"output_{iteration}"
        Path.mkdir(out_dir)
        globs = []
        globs.append( path.glob(self.runoff_pattern) )
        globs.append( path.glob(self.lateral_pattern) )
        globs.append( path.glob(self.terminal_pattern) )
        globs.append( path.glob(self.coastal_pattern) )
        for g in globs:
            for f in g:
                f.rename(out_dir/f.name)
        rpath = path/Path(self.routing_output)
        rpath.rename(out_dir/rpath.name)
