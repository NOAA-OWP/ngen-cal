from __future__ import annotations

import datetime
import typing
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
from ngen.cal import hookimpl

if TYPE_CHECKING:
    from ngen.cal.meta import JobMeta
    from ngen.cal.model import ModelExec
    from ngen.config.realization import NgenRealization


class _NgenCalModelOutputFn(typing.Protocol):
    def __call__(self, id: str) -> pd.Series: ...


@typing.final
class TrouteOutput:
    def __init__(self, filepath: Path) -> None:
        self._output_file = filepath
        self._ngen_realization: NgenRealization | None = None

    def ngen_cal_model_configure(self, config: ModelExec) -> None:
        # avoid circular import
        from ngen.cal.ngen import NgenBase

        assert isinstance(config, NgenBase)
        assert config.ngen_realization is not None
        self._ngen_realization = config.ngen_realization

    # Try external provided output hooks, if those fail, try this one
    # this will only execute if all other hooks return None (or they don't exist)
    @hookimpl(specname="ngen_cal_model_output", trylast=True)
    def get_output(self, id: str) -> pd.Series | None:
        assert self._ngen_realization is not None, "ngen realization required"

        if not self._output_file.exists():
            print(
                f"{self._output_file} not found. Current working directory is {Path.cwd()!s}"
            )
            print("Setting output to None")
            return None

        filetype = self._output_file.suffix.lower()
        if filetype == ".csv":
            fn = self._factory_handler_csv(self._output_file)
        # TODO: fix. dont know if this format still works
        # elif filetype == ".hdf5":
        #     fn = _model_output_legacy_hdf5(self._output_file)
        elif filetype == ".nc":
            fn = _stream_output_netcdf_v1(self._output_file)
        elif filetype == ".parquet":
            fn = _stream_output_parquet_v1(self._output_file)
        else:
            raise RuntimeError(
                f"unsupported t-route output filetype: {self._output_file.suffix}"
            )

        ds = fn(id)
        ds.name = "sim_flow"

        # value time should be realization start_time + output_interval.
        # e.g. start_time: 2020-01-01T00:00Z; output_interval: 3600s
        # series starts at: 2020-01-01T01:00Z
        # first output time is `start_time` + `output_interval`
        ngen_dt = datetime.timedelta(
            seconds=self._ngen_realization.time.output_interval
        )
        start = self._ngen_realization.time.start_time
        ds = ds.loc[start + ngen_dt :]
        ds = ds.resample("1h").first()
        return ds

    def _factory_handler_csv(self, filepath: Path) -> _NgenCalModelOutputFn:
        with filepath.open() as fp:
            header = fp.readline().strip()
        # header should look like:
        # csv_output v1   : ","(0, 'q')","(0, 'v')","(0, 'd')",..."
        # stream_output v1: ",,t0,time,flow,velocity,depth,nudge"
        # stream_output v2: ",,current_time,flow,velocity,depth,nudge"
        if header.startswith(",\"(0, 'q')\""):
            assert self._ngen_realization is not None, "ngen realization required"
            return _csv_output_v1(filepath, self._ngen_realization)
        elif "t0" in header:
            return _stream_output_csv_v1(filepath)
        elif "current_time" in header:
            return _stream_output_csv_v2(filepath)
        raise RuntimeError(f"could not parse t-route csv output file: {filepath!s}")


class NgenSaveOutput:
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
        out_dir = path / f"output_{iteration}"
        Path.mkdir(out_dir)
        globs = []
        globs.append(path.glob(self.runoff_pattern))
        globs.append(path.glob(self.lateral_pattern))
        globs.append(path.glob(self.terminal_pattern))
        globs.append(path.glob(self.coastal_pattern))
        for g in globs:
            for f in g:
                f.rename(out_dir / f.name)
        rpath = path / Path(self.routing_output)
        rpath.rename(out_dir / rpath.name)


def _read_csv_output_v1_no_time(filepath: Path) -> pd.DataFrame:
    # header: ","(0, 'q')","(0, 'v')","(0, 'd')",..."
    # row   : "2420800,0.0,0.0,0.0,..."
    # n_columns = 1 + number of timesteps (`nts`) * 3
    df = pd.read_csv(filepath, index_col=0)
    df.index = df.index.map(lambda x: "wb-" + str(x))
    df.index.name = "waterbody_code"
    tuples = [_parse_column_csv_output_v1(x) for x in df.columns]
    df.columns = pd.MultiIndex.from_tuples(
        tuples, names=("simulation_hour", "variable_name")
    )
    return df


def _parse_column_csv_output_v1(s: str) -> tuple[int, str]:
    # example column: (0, 'q')
    assert s.startswith("(") and s.endswith("')")
    int_end = 0
    char_start = 0
    for i, c in enumerate(s[:-2]):
        if c == ",":
            assert int_end == 0
            int_end = i
        elif c == "'":
            char_start = i
            break

    assert char_start > int_end
    return int(s[1:int_end]), s[char_start + 1 : -2]


def _routing_timestep_size_s(routing_n_ts: int, realization: NgenRealization) -> int:
    """Routing timestep size in seconds."""
    start = realization.time.start_time
    end = realization.time.end_time
    ngen_ts_s = realization.time.output_interval
    # start is not included in interval b.c. first _ngen_ model output is start + dt
    ngen_n_ts = len(pd.date_range(start, end, freq=f"{ngen_ts_s}s", inclusive="right"))

    r_n_ts_in_ngen_ts = routing_n_ts / ngen_n_ts

    r_dt, r = divmod(ngen_ts_s, r_n_ts_in_ngen_ts)
    assert r == 0, "routing timestep is not evenly divisible by ngen_timesteps"
    return int(r_dt)


def _csv_output_v1(p: Path, realization: NgenRealization) -> _NgenCalModelOutputFn:
    df = _read_csv_output_v1_no_time(p)

    columns = typing.cast(pd.MultiIndex, df.columns)
    routing_n_ts = columns.levshape[0]
    routing_ts_s = _routing_timestep_size_s(routing_n_ts, realization)

    r_dt = datetime.timedelta(seconds=routing_ts_s)
    # first output time is `start_time` + `output_interval`
    start = realization.time.start_time
    end = realization.time.end_time

    r_dt_range = pd.date_range(start, end, freq=r_dt, inclusive="right")

    def get_output(id: str) -> pd.Series:
        ds = df.loc[id, (slice(None), "q")]
        ds.index = r_dt_range
        return ds

    return get_output


# change from v1-v2 introduced in https://github.com/NOAA-OWP/t-route/pull/818
def _stream_output_csv_v1(p: Path) -> _NgenCalModelOutputFn:
    # header: ",,t0,time,flow,velocity,depth,nudge"
    # row   : "6680,wb,2010-10-01 00:00:00,1:00:00,0.0,0.0,0.0,-9999.0"
    df = pd.read_csv(p)
    # 't0' is reference time
    df["t0"] = pd.to_datetime(df["t0"])
    # 'time' is the forecast hour
    df["time"] = pd.to_timedelta(df["time"])
    df["value_time"] = df["t0"] + df["time"]
    df.rename(columns={"flow": "value", df.columns[0]: "waterbody_code"}, inplace=True)
    df["waterbody_code"] = df["waterbody_code"].map(lambda x: f"wb-{x}")
    df.set_index("value_time", inplace=True)

    def get_output(id: str) -> pd.Series:
        return df.loc[df["waterbody_code"] == id, "value"]

    return get_output


# change from v1-v2 introduced in https://github.com/NOAA-OWP/t-route/pull/818
def _stream_output_csv_v2(p: Path) -> _NgenCalModelOutputFn:
    # header: ",,current_time,flow,velocity,depth,nudge"
    # row   : "6680,wb,2010-10-01 1:00:00,0.0,0.0,0.0,-9999.0"
    df = pd.read_csv(p)
    df["value_time"] = pd.to_datetime(df["current_time"])
    df.rename(columns={"flow": "value", df.columns[0]: "waterbody_code"}, inplace=True)
    df["waterbody_code"] = df["waterbody_code"].map(lambda x: f"wb-{x}")
    df.set_index("value_time", inplace=True)

    def get_output(id: str) -> pd.Series:
        return df.loc[df["waterbody_code"] == id, "value"]

    return get_output


# TODO: doc when change was made
# TODO: revist
def _model_output_legacy_hdf5(p: Path) -> pd.DataFrame:
    df = pd.read_hdf(p)
    df.index = df.index.map(lambda x: "wb-" + str(x))
    df.columns = pd.MultiIndex.from_tuples(df.columns)
    return df


def _stream_output_netcdf_v1(p: Path) -> _NgenCalModelOutputFn:
    # NOTE: guarded import this is optional feature
    try:
        import xarray as xr
    except ImportError as e:
        raise RuntimeError(
            "`ngen.cal` not installed with `netcdf` support. Re-install with feature flag `[netcdf]`"
        ) from e

    ds = xr.open_dataset(p)
    flow = ds.get("flow")
    assert flow is not None

    df: pd.DataFrame = flow.to_dataframe()
    df.reset_index(inplace=True)

    expected_columns = ["feature_id", "time", "flow"]
    assert df.columns.isin(expected_columns).sum() == len(expected_columns)

    df.rename(
        columns={"flow": "value", "time": "value_time", "feature_id": "waterbody_code"},
        inplace=True,
    )
    df["waterbody_code"] = df["waterbody_code"].map(lambda x: f"wb-{x}")
    df.set_index("value_time", inplace=True)

    def get_output(id: str) -> pd.Series:
        return df.loc[df["waterbody_code"] == id, "value"]

    return get_output


def _stream_output_parquet_v1(p: Path) -> _NgenCalModelOutputFn:
    #    location_id value value_time           variable_name units reference_time configuration
    # 0  wb-2420800  0.0   2023-04-02 00:05:00  streamflow    m3/s  2023-04-02     None
    # 1  wb-2420800  0.0   2023-04-02 00:05:00  velocity      m/s   2023-04-02     None
    # 2  wb-2420800  0.0   2023-04-02 00:05:00  depth         m     2023-04-02     None
    df = pd.read_parquet(p)
    df.set_index("value_time", inplace=True)

    def get_output(id: str) -> pd.Series:
        return df.loc[
            (df["location_id"] == id) & (df["variable_name"] == "streamflow"), "value"
        ]

    return get_output
