from typing import Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from ngen.config_gen.hook_providers import HookProvider

from pydantic import BaseModel

from ngen.config.init_config.pet import PET, PetMethod


# `PetHooks` implicitly satisfies the `HydrofabricLinkedDataHook`, `BuilderVisitable` interfaces (`typing.Protocol`s).
# You can "inherit" from these interfaces if so desired.
# This can be helpful during development as static analysis tools will tell you if your type satisfies the interfaces.
#
# from ngen.config_gen.hooks import HydrofabricLinkedDataHook, BuilderVisitable
# class PetHooks(HydrofabricLinkedDataHook, BuilderVisitable): # this is equivalent
class PetHooks:
    def __init__(self):
        self.data = {}
        self.__version = None

    def _set_version(self, version: str):
        if self.__version is None:
            self.__version = version
        elif self.__version != version:
            raise RuntimeError(
                f'mismatched versions. current="{self.__version}" new="{version}"'
            )

    def _version(self) -> str:
        if self.__version is None:
            raise RuntimeError("no version set")
        return self.__version

    def _v2_linked_data_hook(self, data: Dict[str, Any]):
        # NOTE typo in forcing metadata name
        self.data["longitude_degrees"] = data["X"]
        self.data["latitude_degrees"] = data["Y"]
        self.data["site_elevation_m"] = data["elevation_mean"]

    def hydrofabric_linked_data_hook(
        self, version: str, divide_id: str, data: Dict[str, Any]
    ) -> None:
        self._set_version(version)
        if self._version() == "2.0":
            self._v2_linked_data_hook(data)
        else:
            raise RuntimeError("only support v2 hydrofabric")

    def _v2_defaults(self) -> None:
        # TODO: this was from old code, not sure what to do here
        # if not bool(values["yes_aorc"]):
        #     return values
        self.data["yes_wrf"] = False
        self.data["wind_speed_measurement_height_m"] = 10.0
        self.data["humidity_measurement_height_m"] = 10.0
        self.data["shortwave_radiation_provided"] = False
        self.data["time_step_size_s"] = 3600
        self.data["num_timesteps"] = 720
        self.data["cloud_base_height_known"] = False

        self.data["verbose"] = True
        # TODO: think of how to get user input for fields like this
        self.data["pet_method"] = PetMethod.energy_balance
        # TODO: revisit this. I think this is telling it to use BMI
        self.data["yes_aorc"] = True

        # TODO: FIGURE OUT HOW TO GET THESE PARAMETERS
        # BELOW PARAMETERS MAKE NO SENSE
        self.data["vegetation_height_m"] = 0.12
        self.data["zero_plane_displacement_height_m"] = 0.0003
        self.data["momentum_transfer_roughness_length"] = 0.0
        self.data["heat_transfer_roughness_length_m"] = 0.1
        self.data["surface_longwave_emissivity"] = 42.0
        self.data["surface_shortwave_albedo"] = 7.0

    def build(self) -> BaseModel:
        return PET(**self.data)

    def visit(self, hook_provider: "HookProvider") -> None:
        # call `HookProvider` method(s) and pass `self` for any `Hook`s defined on `PetHooks`.
        #
        # i.e. `PetHooks` defines the `hydrofabric_linked_data_hook`, so call its `HookProvider`
        # counterpart `provide_hydrofabric_linked_data` with self as the argument.
        hook_provider.provide_hydrofabric_linked_data(self)

        if self._version() != "2.0":
            raise RuntimeError("only support v2 hydrofabric")
        self._v2_defaults()


if __name__ == "__main__":
    import geopandas as gpd
    import pandas as pd

    from ngen.config_gen.hook_providers import DefaultHookProvider
    from ngen.config_gen.file_writer import DefaultFileWriter
    from ngen.config_gen.generate import generate_configs

    hf_file = "/Users/austinraney/Downloads/nextgen_09.gpkg"
    hf_lnk_file = "/Users/austinraney/Downloads/nextgen_09.parquet"

    hf: gpd.GeoDataFrame = gpd.read_file(hf_file, layer="divides")
    hf_lnk_data: pd.DataFrame = pd.read_parquet(hf_lnk_file)

    subset = [
        "cat-1529608",
        "cat-1537245",
        "cat-1529607",
        "cat-1536906",
        "cat-1527290",
    ]

    hf = hf[hf["divide_id"].isin(subset)]
    hf_lnk_data = hf_lnk_data[hf_lnk_data["divide_id"].isin(subset)]

    hook_provider = DefaultHookProvider(hf=hf, hf_lnk_data=hf_lnk_data)
    file_writer = DefaultFileWriter("./config/")

    # the goal of ngen.config_gen is to provide a framework for creating model configuration files.
    # all model configuration files are made up of data. often this data comes from a variety of
    # "sources". for example, there may be fields like catchment centroid or wind speed measurement
    # height that could be sourced from geographic data (think the hydrofabric) or the metadata of
    # whatever forcing product will be used for the simulation. in both instances, the hydrofabric
    # data and the forcing metadata are _sources_ of information that can be used to fill model
    # configuration fields. there may also be fields like start and end time that are specific to a
    # given simulation, but may be _sourced_ from other kinds of _sources_ think a command line
    # argument or a separate configuration file like a NextGen realization config.
    #
    # in all of these examples, there are data sources _can_ use to create a model's configuration
    # file. the questions then are, what data sources are available? how does a model tell you what
    # data sources it needs? and how does a model give you a built configuration file? to address
    # this, ngen.config_gen has the concept of _hooks_. hooks are a way of providing data from a
    # source to some other code that uses that data to build a configuration file. hooks are also a
    # way for some code to tell us what data it _needs_ to build a configuration file.  some models
    # may only need a limited amount of information from a single hook to generate a configuration
    # file, while another might need all the available hooks. ngen.config_gen offers hooks that
    # provide data from data sources like the hydrofabric, hydrofabric linked data, and forcing
    # metadata. so, to answer the prior stated questions:
    #
    # - what data sources are available?
    #       whatever hooks are available
    # - how does a model tell you what data sources it needs?
    #       they specify the hooks they need
    # - how does a model give you a built configuration file?
    #       more on this later, but the code that generates the config implements a `build()` method
    #       that returns a built configuration file
    #
    # what is a hook anyways? well in the context of ngen.config_gen, a hook is just a _method_ that
    # follows a certain interface. for example the `hydrofabric_linked_data_hook` has the interface:
    #
    # ```python
    # def hydrofabric_linked_data_hook(self, version: str, divide_id: str, data: Dict[str, Any]) -> None:
    #     pass
    # ```
    #
    # the `hydrofabric_linked_data_hook` takes in a version string (e.g. "2.0"), a dictionary of
    # hydrofabric linked field names to their values, and the divide id of the data dictionary.
    # you can imagine an instance of this class might extract certain values from the data
    # dictionary and perhaps transform the values and then store those values in its own dictionary.
    # you could also imagine that the class might do different things based on the version of the
    # source data it received. for example, in an older version a model configuration field must be
    # computed, but in a newer version the field is in the hydrofabric linked data and can just be used.
    # a listing of all available hooks can be found [here](#TODO).
    #
    # the general idea is that you define a class, here `PetHooks`, and add any `Hook` methods
    # required to create a model's BMI init configuration file. some other code will call a `visit`
    # method on your class with a `HookProvider` instance. The `HookProvider` has methods that
    # correspond to each hook. In your `visit` method, for each hook _your_ class implements you
    # call the corresponding `HookProvider` method and pass `self` as the argument. The
    # `HookProvider` will then call the corresponding `Hook` method on your class and _provide_ it
    # with data to satisfy that hook (e.g. information from the HydroFabric) _for a single catchment_.
    # for example, a snippet of the above `PetHooks` class's `visit` method looks like:
    #
    # ```python
    # def visit(self, hook_provider: "HookProvider") -> None:
    #     # i.e. `PetHooks` defines the `hydrofabric_linked_data_hook`, so call its `HookProvider`
    #     # counterpart `provide_hydrofabric_linked_data` with self as the argument.
    #     hook_provider.provide_hydrofabric_linked_data(self)
    # ```
    #
    # your hook
    # and provide it with data that you use to create a model's catchment scale init config file.
    # in this example, we are creating init config files for the `Pet` model. the data needed to
    # create a config file mostly lives in the hydrofabric linked data (.parquet files), so to get
    # that data, the `hydrofabric_linked_data_hook` method is specified on the class. this can be
    # thought of a telling the configuration generation code, what data you _need_ to create a
    # config.
    #
    # a hook is just method on your class that follows a certain interface. for example, the
    # `hydrofabric_linked_data_hook` has the interface:
    #
    # ```python
    # def hydrofabric_linked_data_hook(
    #     self, version: str, divide_id: str, data: Dict[str, Any]
    # ) -> None:
    # ```
    # here,
    #
    # next you add a `visit` method to your class. The visit method takes two parameters, `self` and
    # `hook_provider`. The role of the `visit` method is to tell the `hook_provider` what hooks

    # the general idea is a hook provider can fulfill any hook

    generate_configs(
        hook_providers=hook_provider,
        hook_objects=[PetHooks],
        file_writer=file_writer,
    )
