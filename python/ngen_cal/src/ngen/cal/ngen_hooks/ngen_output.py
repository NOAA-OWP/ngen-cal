from __future__ import annotations

from ngen.cal import hookimpl

import pandas as pd
from pandas import DataFrame, Series
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ngen.cal.meta import JobMeta

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ngen.cal.meta import JobMeta

class TrouteOutput:

    def __init__(self, filepath: Path) -> None:
        self._output_file = filepath
        self._type = filepath.suffix

    def _get_dataframe(self) -> DataFrame | None:
        """Get the t-route output raw dataframe from either csv or hdf5 files

        Returns:
            DataFrame: _description_
        """
        if self._type == '.csv':
            df = pd.read_csv(self._output_file, index_col=0)
            df.index = df.index.map(lambda x: 'wb-'+str(x))
            tuples = [ eval(x) for x in df.columns ]
            df.columns = pd.MultiIndex.from_tuples(tuples)
        elif self._type == '.hdf5':
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
        try:
            #look for routed data
            #read the routed flow at the given id
            df = self._get_dataframe()

            df = df.loc[id]
            output = df.xs('q', level=1, drop_level=False)
            #This is a hacky way to get the time index...pass the time around???
            tnx_file = list(Path(self._output_file).parent.glob("nex*.csv"))[0]
            tnx_df = pd.read_csv(tnx_file, index_col=0, parse_dates=[1], names=['ts', 'time', 'Q']).set_index('time')
            dt_range = pd.date_range(tnx_df.index[0], tnx_df.index[-1], len(output.index)).round('min')
            output.index = dt_range
            #this may not be strictly nessicary...I think the _evalutate will align these...
            output = output.resample('1h').first()
            output.name="sim_flow"
            return output
        except FileNotFoundError:
            print(f"{self._output_file} not found. Current working directory is {Path.cwd()}")
            print("Setting output to None")
            return None
        except Exception as e:
            raise(e)

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
