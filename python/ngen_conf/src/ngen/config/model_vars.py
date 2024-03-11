"""
This module contains functions and abstractions for representing and resolving NextGen BMI module
input and output variables.

Functions of note:
- `resolve_model_inputs`: Returns the input mappings and missing inputs for a single model.
- `resolve_inputs_mapping`: Returns the input mappings and missing inputs for a list of models (often, multi-bmi).
- `resolve_outputs_mapping`: Returns the set of invalid output names / aliases for a list of models.

Classes of note:
- `Var`: Represents the concept of a NextGen BMI variable.
- `Inputs`: Represents the input variables and alias re-mappings of a NextGen BMI module.
- `Outputs`: Represents the output variables and alias mappings of a NextGen BMI module.
- `InputsBuilder`: Builder object for creating new `Inputs` instances.
- `OutputsBuilder`: Builder object for creating new `Outputs` instances.
"""
from __future__ import annotations

import collections
import copy
import dataclasses
import typing

import typing_extensions
from typing_extensions import Self


class ModelInputMeta(typing_extensions.Protocol):
    """
    The name of a BMI module and it's inputs
    """

    def name(self) -> str:
        ...

    def inputs(self) -> Inputs:
        ...


class ModelOutputMeta(typing_extensions.Protocol):
    """
    The name of a BMI module and it's outputs
    """

    def name(self) -> str:
        ...

    def outputs(self) -> Outputs:
        ...


class ModelMeta(typing_extensions.Protocol):
    """
    The name of a BMI module and it's inputs and outputs
    """

    def name(self) -> str:
        ...

    def inputs(self) -> Inputs:
        ...

    def outputs(self) -> Outputs:
        ...


@dataclasses.dataclass
class Var:
    """
    Structure that captures the concept of a NextGen BMI variable.
    """

    name: str


class Inputs:
    """
    Representation of a NextGen BMI module's input variables and alias re-mappings.

    The general rules NextGen enforces for input variables are:
    - all inputs must receive data from some provider (e.g. forcing, a previous module)
    - an alias to an input name will always be used. only alias will be used to locate data provider
    - inputs can have the same alias name (i.e. 2 inputs receive data from same provider)
    - alias to an input name that does not exist is a no-op (alias is ignored)
    - only the first provided alias to an input name is used

    The general rules NextGen enforces for input variables in a Multi-BMI formulation are:
    - input names and aliases are module scoped (i.e. ok to have 2 modules with same input name)

    Example:
        inputs = InputsBuilder().add_input(
            Var(name="APCP_surface"), "atmosphere_water__rainfall_volume_flux"
        ).build()

        assert inputs.resolve_name("APCP_surface") == "atmosphere_water__rainfall_volume_flux"

        assert inputs.var("APCP_surface") == Var(name="APCP_surface")

        assert inputs.mapping() == {"APCP_surface": "atmosphere_water__rainfall_volume_flux"}

        assert list(inputs.inputs()) == [Var(name="APCP_surface")]
    """

    def __init__(self):
        # mapping of var name to _VarAliasPair
        self._inputs: dict[str, _VarAliasPair] = dict()
        self._mapping: dict[str, str] | None = None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(inputs={self._inputs})"

    def resolve_name(self, name: str) -> str:
        """
        Return alias if it exists or the input's name
        `KeyError` if the name is not mapped.
        """
        var = self._get_input(name)
        if var is None:
            # probably should just warn here and return name
            raise KeyError(f"var {name!r} does not exist")
        return var.resolve_name()

    def var(self, name: str) -> Var:
        """
        Get the Var instance mapped to a given input name.

        `KeyError` if the name is not mapped.
        """
        var = self._get_input(name)
        if var is None:
            # probably should just warn here and return name
            raise KeyError(f"var {name!r} does not exist")
        return var.var

    def mapping(self) -> dict[str, str]:
        """
        Return mapping of var name to alias name.
        If an alias does not exist, mapping is from var name to var name.
        """
        if self._mapping is None:
            self._mapping = {
                name: var.resolve_name() for name, var in self._inputs.items()
            }
        return self._mapping

    def inputs(self) -> typing.Iterator[Var]:
        """
        Iterator of Var's in Input instance
        """
        return (var.var for var in self._inputs.values())

    def _add_input(self, *, input: Var, alias: str | None = None):
        """
        Add input and potentially an alias.
        Overwrites an existing input with the same name.

        Note: this is private to explicitly separate creation from usage.
        """
        self._inputs[input.name] = _VarAliasPair(var=input, alias=alias)

    def _add_alias(self, *, name: str, alias: str):
        """
        Add an alias to an existing input.

        Overwrites an existing alias if it exists. For example, if input with
        name `Q` has existing alias `q` and `_add_alias("Q", "discharge")` is
        called, `Q`'s alias will be changed.

        `KeyError` if input does not exist.

        Note: this is private to explicitly separate creation from usage.
        """
        input = self._get_input(name)
        if input is None:
            # probably should just warn here that it is a no-op
            raise KeyError(f"input: {name!r} does not exist")
        input.alias = alias

    def __iter__(self) -> typing.Iterator[Var]:
        return self.inputs()

    def _get_input(self, name: str) -> _VarAliasPair | None:
        """
        Get _VarAliasPair given a name.
        """
        return self._inputs.get(name)


class Outputs:
    """
    Representation of a NextGen BMI module's output variables and alias mappings.

    The general rules NextGen enforces for output variables are:
    - output names and aliases must be unique
    - an output name can have multiple aliases

    The general rules NextGen enforces for output variables in a Multi-BMI formulation are:
    - module's requiring data as input can refer to other module's output by name _or_ aliases.
    - edge cases: if 2+ modules have the same output name:
        - if all modules alias the output name and another module requires input data by output
        _name_, the first module in the modules list with the output name will provide data.
        - if all _but one_ module aliases the output name and another module requires input data
        by output _name_, the module that _does not_ define an alias will provide data.

    For other information see
    [NextGen Docs](https://github.com/NOAA-OWP/ngen/blob/master/doc/BMI_MODELS.md#optional-parameters).

    Example:
        outputs = OutputsBuilder().add_output(
            Var(name="ETRAN"), "land_vegetation_canopy_water__transpiration_volume_flux"
        ).build()

        assert outputs.resolve_var("ETRAN") == Var(name="ETRAN")
        assert outputs.resolve_var(
            "land_vegetation_canopy_water__transpiration_volume_flux"
        ) == Var(name="ETRAN")

        assert outputs.mapping() == {"ETRAN": {"ETRAN", "land_vegetation_canopy_water__transpiration_volume_flux"}}

        assert list(outputs.outputs()) == [Var(name="ETRAN")]

        assert list(outputs.names()) == ["ETRAN", "land_vegetation_canopy_water__transpiration_volume_flux"]

        assert outputs.alias("ETRAN") == Var(name="ETRAN")

        assert outputs.var("ETRAN") == Var(name="ETRAN")
    """

    def __init__(self):
        # mapping of name or alias to Var instance
        self._outputs: dict[str, Var] = dict()
        self._mapping: dict[str, set[str]] | None = None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(outputs={self._outputs})"

    def resolve_var(self, name_or_alias: str) -> Var | None:
        """
        Given a name _or_ alias, return the associated output var if it exists.
        """
        return self._get_output(name_or_alias)

    def mapping(self) -> dict[str, set[str]]:
        """
        Return mapping of output var name to it's aliases and itself.
        """
        if self._mapping is None:
            mapping: dict[str, set[str]] = collections.defaultdict(set)
            for name_or_alias, var in self._outputs.items():
                mapping[var.name].add(name_or_alias)
            self._mapping = mapping
        return dict(self._mapping)

    def outputs(self) -> typing.Iterator[Var]:
        """
        Iterator of output Vars. Does not include aliases.
        """
        return (var for name, var in self._outputs.items() if name == var.name)

    def names(self) -> typing.Iterator[str]:
        """
        Iterator of all output Var and alias names.
        """
        return (name for name in self._outputs.keys())

    def _add_output(self, *, output: Var, alias: str | None = None):
        """
        Add output and potentially an alias.
        `KeyError` if `output` var _or_ `alias` mapping already exists.

        Note: this is private to explicitly separate creation from usage.
        """
        if output.name in self._outputs:
            raise KeyError(f"output: {output.name!r} already exists")
        if alias in self._outputs:
            raise KeyError(f"alias: {alias!r} already exists")
        if alias is not None:
            self._outputs[alias] = output
        self._outputs[output.name] = output

    def _add_alias(self, *, name: str, alias: str):
        """
        Add an alias to an existing output.

        `KeyError` if `output` mapping _does not_ exist.
        `KeyError` if `alias` mapping already exists.

        Note: this is private to explicitly separate creation from usage.
        """
        if alias in self._outputs:
            raise KeyError(f"alias: {alias!r} already exists")

        output = self._get_output(name)
        if output is None:
            raise KeyError(f"output: {name!r} does not exist")

        self._outputs[alias] = output

    def _get_output(self, name: str) -> Var | None:
        """
        Get Var given a name.
        """
        return self._outputs.get(name)

    def _is_mapped(self, name_or_alias: str) -> bool:
        """
        Test if a name / alias is mapped.
        """
        return name_or_alias in self._outputs


class InputsBuilder:
    """
    Builder object for creating new `Inputs` instances.

    Example:
        InputsBuilder().add_input(Var(name="APCP_surface")).build()

        # alias `APCP_surface` as `atmosphere_water__rainfall_volume_flux`.
        inputs = (
            InputsBuilder()
            .add_input(Var(name="APCP_surface"))
            .add_alias("APCP_surface", "atmosphere_water__rainfall_volume_flux")
            .build()
        )
        # or like this
        inputs = InputsBuilder().add_input(
            Var(name="APCP_surface"), "atmosphere_water__rainfall_volume_flux"
        ).build()
    """

    def __init__(self):
        self._inputs = Inputs()

    @classmethod
    def from_inputs(cls, inputs: Inputs) -> Self:
        """
        Create a new `InputBuilder` from an existing `Inputs`.

        Safety: `inputs` is deep copied, so it is safe to use and mutate
                after calling this.
        """
        inst = cls()
        inst._inputs = copy.deepcopy(inputs)
        return inst

    def add_input(self, input: Var, alias: str | None = None) -> Self:
        """
        Add input and potentially an alias.
        Overwrites an existing input with the same name.
        """
        self._inputs._add_input(input=input, alias=alias)
        return self

    def add_alias(self, name: str, alias: str) -> Self:
        """
        Add an alias to an existing input.

        Overwrites an existing alias if it exists. For example, if input with
        name `Q` has existing alias `q` and `add_alias("Q", "discharge")` is
        called, `Q`'s alias will be changed.

        `KeyError` if `name` does not exist.
        """
        self._inputs._add_alias(name=name, alias=alias)
        return self

    def build(self) -> Inputs:
        """
        Returns a new `Inputs` instance.

        Safety: successive calls return new objects. So, it is safe to add
                inputs, build, then add more inputs.
        """
        return copy.deepcopy(self._inputs)


class OutputsBuilder:
    def __init__(self):
        self._outputs = Outputs()

    @classmethod
    def from_outputs(cls, outputs: Outputs) -> Self:
        """
        Create a new `OutputsBuilder` from an existing `Outputs`.

        Safety: `outputs` is deep copied, so it is safe to use and mutate after
                calling this.
        """
        inst = cls()
        inst._outputs = copy.deepcopy(outputs)
        return inst

    def add_output(self, output: Var, *aliases: str) -> Self:
        """
        Add output and potentially aliases.
        Overwrites an existing input with the same name.

        `KeyError` if `output` var _or_ any `alias` mapping already exists.
        """
        self._outputs._add_output(output=output)
        self.add_alias(output.name, *aliases)
        return self

    def add_alias(self, name: str, *aliases: str) -> Self:
        """
        Add aliases to a given output.

        `KeyError` if any alias mapping already exists. No aliases will be
         created if any alias already exists.
        `KeyError` if `name` mapping _does not_ exist.
        """
        for alias in aliases:
            if self._outputs._is_mapped(alias):
                raise KeyError(f"alias: {alias!r} already exists")

        for alias in aliases:
            self._outputs._add_alias(name=name, alias=alias)
        return self

    def build(self) -> Outputs:
        """
        Returns a new `Outputs` instance.

        Safety: successive calls return new objects. So, it is safe to add
                outputs, build, then add more outputs.
        """
        return copy.deepcopy(self._outputs)


class _VarAliasPair:
    def __init__(self, var: Var, alias: str | None = None):
        self.var: Var = var
        # alias never has value var.name
        self._alias: str | None = None if alias == var.name else alias

    def resolve_name(self) -> str:
        """Return alias is it exists or the input's name"""
        if self.alias is not None:
            return self.alias
        return self.var.name

    @property
    def alias(self) -> str | None:
        """
        Invariant: alias does not equal `var.name`
        """
        return self._alias

    @alias.setter
    def alias(self, value: str | None) -> None:
        if value == self.var.name:
            value = None
        self._alias = value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(var={self.var!r}, alias={self.alias!r})"


@dataclasses.dataclass
class ModelVarMapping:
    """
    The name of a model and one of it's Var's.
    """

    model: str
    var: Var


@dataclasses.dataclass
class VarMapping:
    """
    Structure that captures the concept of a source variable on some model, a destination variable
    on some model, and a binding variable, `via`. Call `str()` on an instance for a visual
    representation.

    Graphically:
        src(model::var) -> via -> dest(model::var)
    """

    src: ModelVarMapping
    dest: ModelVarMapping
    via: str

    def is_src_alias(self) -> bool:
        return self.src.var.name != self.via

    def is_dest_alias(self) -> bool:
        return self.dest.var.name != self.via

    @typing_extensions.override
    def __str__(self) -> str:
        input_alias = f" as {self.via}" if self.is_src_alias() else ""
        dest_alias = f" as {self.via}" if self.is_dest_alias() else ""
        return f"{self.src.model}::{self.src.var.name}{input_alias} -> {self.dest.model}::{self.dest.var.name}{dest_alias}"


def resolve_model_inputs(
    model: ModelInputMeta, data_providers: typing.Iterable[ModelOutputMeta]
) -> tuple[list[VarMapping], list[Var]]:
    """
    Return a tuple of valid input variable mappings and missing input variables mappings.
    Aliases are accounted for.
    """
    # input var name -> src dest mapping
    mapping: dict[str, VarMapping] = dict()
    # input var name -> Var
    maybe_missing: dict[str, Var] = dict()
    for dest_name, dest_name_or_alias in model.inputs().mapping().items():
        dest = ModelVarMapping(model=model.name(), var=model.inputs().var(dest_name))
        for source in data_providers:
            if dest_name in mapping:
                assert dest_name not in maybe_missing
                m = mapping[dest_name]
                # only pick up new mappings if:
                # - src provides data and has no aliases. follows that prev has an alias
                src_aliases = source.outputs().mapping().get(m.src.var.name)
                if src_aliases is not None and len(src_aliases) > 1:
                    continue

            var = source.outputs().resolve_var(dest_name_or_alias)
            if var is not None:
                src = ModelVarMapping(model=source.name(), var=var)
                mapping[dest_name] = VarMapping(
                    via=dest_name_or_alias, src=src, dest=dest
                )

            if dest_name not in mapping:
                maybe_missing[dest_name] = dest.var
            else:
                maybe_missing.pop(dest_name, None)

    return list(mapping.values()), list(maybe_missing.values())


def resolve_inputs_mapping(
    *models: ModelMeta,
) -> tuple[dict[str, list[VarMapping]], dict[str, list[Var]]]:
    """
    Return a tuple of model name to valid input variable mappings and model name to missing input
    variable mappings. Aliases are accounted for.
    """
    model_mapping: dict[str, list[VarMapping]] = collections.defaultdict(list)
    missing: dict[str, list[Var]] = collections.defaultdict(list)
    i = 1
    for model in models[1:]:
        mapped, unmapped = resolve_model_inputs(model, models[:i])
        if mapped:
            model_mapping[model.name()] = mapped
        if unmapped:
            missing[model.name()] = unmapped
        i += 1
    return dict(model_mapping), dict(missing)


def resolve_outputs_mapping(models: typing.Iterable[ModelOutputMeta]) -> set[str]:
    """
    Validate a list of models follow NextGen's output variable invariants.
    Returns the set of invalid output names / aliases.
    """
    duplicated: set[str] = set()
    total: set[str] = set()

    for model in models:
        for name, aliases in model.outputs().mapping().items():
            for alias in aliases:
                if len(aliases) == 1:
                    assert name == alias
                # mapping contains mappings to alias _and_ name itself
                # if mappings contains alias(es) don't account for self reference
                if alias == name and len(aliases) > 1:
                    continue
                if alias in total:
                    duplicated.add(alias)
                else:
                    total.add(alias)

    return duplicated
