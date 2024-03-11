from __future__ import annotations

import pytest

from ngen.config.model_vars import (
    Inputs,
    InputsBuilder,
    ModelMeta,
    Outputs,
    OutputsBuilder,
    Var,
    VarMapping,
    resolve_inputs_mapping,
    resolve_outputs_mapping,
)


class Model(ModelMeta):
    def __init__(self, name: str, inputs: Inputs, outputs: Outputs):
        self._name: str = name
        self._inputs: Inputs = inputs
        self._outputs: Outputs = outputs

    def name(self) -> str:
        return self._name

    def inputs(self) -> Inputs:
        return self._inputs

    def outputs(self) -> Outputs:
        return self._outputs

    def __repr__(self) -> str:
        return f"Model(name={self._name}, inputs={str(self._inputs)}, outputs={str(self._outputs)})"


VALIDATE_OUTPUT_MAPPING_CASES = [
    (
        # model 1 Outputs
        OutputsBuilder().build(),
        # model 2 Outputs
        OutputsBuilder().build(),
        # expected
        set(),
    ),
    (
        OutputsBuilder().build(),
        OutputsBuilder().add_output(Var(name="a")).build(),
        set(),
    ),
    (
        OutputsBuilder().add_output(Var(name="a")).build(),
        OutputsBuilder().add_output(Var(name="b")).build(),
        set(),
    ),
    (
        OutputsBuilder().add_output(Var(name="a"), "b").build(),
        OutputsBuilder().add_output(Var(name="b"), "a").build(),
        set(),
    ),
    (
        OutputsBuilder().add_output(Var(name="b")).build(),
        OutputsBuilder().add_output(Var(name="b"), "a").build(),
        set(),
    ),
    (
        OutputsBuilder().add_output(Var(name="b"), "a").build(),
        OutputsBuilder().add_output(Var(name="b")).build(),
        set(),
    ),
    (
        OutputsBuilder().add_output(Var(name="a"), "b").build(),
        OutputsBuilder().add_output(Var(name="b")).build(),
        {"b"},
    ),
    (
        OutputsBuilder().add_output(Var(name="a")).build(),
        OutputsBuilder().add_output(Var(name="a")).build(),
        {"a"},
    ),
]


@pytest.mark.parametrize("a_outputs, b_outputs, same", VALIDATE_OUTPUT_MAPPING_CASES)
def test_validate_output_mapping(
    a_outputs: Outputs, b_outputs: Outputs, same: set[str]
):
    mod1 = Model(
        name="mod1",
        inputs=Inputs(),
        outputs=a_outputs,
    )
    mod2 = Model(
        name="mod2",
        inputs=Inputs(),
        outputs=b_outputs,
    )
    assert resolve_outputs_mapping([mod1, mod2]) == same
    assert resolve_outputs_mapping([mod2, mod1]) == same


def test_inputs():
    var = Var(name="a")
    inputs = InputsBuilder().add_input(var).build()
    assert list(inputs.inputs()) == [var]
    assert inputs.mapping() == {var.name: var.name}
    assert inputs.resolve_name(var.name) == var.name
    assert inputs.var(var.name) == var

    a, a_alias = Var(name="a"), "b"
    b, b_alias = Var(name="b"), "a"
    inputs = InputsBuilder().add_input(a, a_alias).add_input(b, b_alias).build()
    assert list(inputs.inputs()) == [a, b]
    assert inputs.mapping() == {a.name: a_alias, b.name: b_alias}

    assert inputs.resolve_name(a.name) == a_alias
    assert inputs.resolve_name(b.name) == b_alias

    assert inputs.var(a.name) == a
    assert inputs.var(b.name) == b


INPUTS_ALIAS_CASES = [
    (
        InputsBuilder().add_input(Var(name="a"), "b").build(),
        Var(name="a"),
        "b",
    ),
    (
        InputsBuilder().add_input(Var(name="a")).add_alias("a", "b").build(),
        Var(name="a"),
        "b",
    ),
]


@pytest.mark.parametrize("inputs, var, alias", INPUTS_ALIAS_CASES)
def test_inputs_alias(inputs: Inputs, var: Var, alias: str):
    assert list(inputs.inputs()) == [var]
    assert inputs.mapping() == {var.name: alias}
    assert inputs.resolve_name(var.name) == alias
    assert inputs.var(var.name) == var


def test_outputs():
    var = Var(name="a")
    outputs = OutputsBuilder().add_output(var).build()
    assert list(outputs.outputs()) == [var]
    assert outputs.mapping() == {"a": {"a"}}
    assert list(outputs.names()) == ["a"]
    assert outputs.resolve_var(var.name) == var

    var, alias = Var(name="a"), "b"
    outputs = OutputsBuilder().add_output(var, alias).build()
    assert list(outputs.outputs()) == [var]
    assert outputs.mapping() == {"a": {"a", "b"}}
    assert list(outputs.names()) == ["a", "b"]
    assert outputs.resolve_var(var.name) == var
    assert outputs.resolve_var(alias) == var


def test_outputs_multi_with_alias():
    var_a, b = Var(name="a"), "b"
    var_c, d = Var(name="c"), "d"
    outputs = OutputsBuilder().add_output(var_a, b).add_output(var_c, d).build()
    assert list(outputs.outputs()) == [var_a, var_c]
    assert outputs.mapping() == {"a": {"a", "b"}, "c": {"c", "d"}}
    assert sorted(list(outputs.names())) == ["a", "b", "c", "d"]

    assert outputs.resolve_var(var_a.name) == var_a
    assert outputs.resolve_var(b) == var_a

    assert outputs.resolve_var(var_c.name) == var_c
    assert outputs.resolve_var(d) == var_c


def test_outputs_raises_duplicate_variable():
    a, a_alias = Var(name="a"), "b"
    b = Var(name="b")
    with pytest.raises(KeyError, match="'b' already exists"):
        OutputsBuilder().add_output(a, a_alias).add_output(b).build()


def test_outputs_raises_duplicate_variable_by_alias():
    a, a_alias = Var(name="a"), "b"
    b, b_alias = Var(name="b"), "a"
    builder = OutputsBuilder().add_output(a).add_output(b)
    with pytest.raises(KeyError, match=f"'{a_alias}' already exists"):
        builder.add_alias(a.name, a_alias)

    with pytest.raises(KeyError, match=f"'{b_alias}' already exists"):
        builder.add_alias(b.name, b_alias)


def test_validate_input_mapping_simple():
    via = "input"
    forcing_var = Var(name=via)
    forcing = Model(
        name="forcing",
        inputs=Inputs(),
        outputs=OutputsBuilder().add_output(forcing_var).build(),
    )

    a_input_var = Var(name=via)
    a = Model(
        name="a",
        inputs=InputsBuilder().add_input(a_input_var).build(),
        outputs=OutputsBuilder().add_output(Var(name="output")).build(),
    )
    valid, unset = resolve_inputs_mapping(forcing, a)

    assert len(unset) == 0

    assert a.name() in valid
    assert len(valid[a.name()]) == 1
    mapping = valid[a.name()][0]
    assert mapping.src.model == forcing.name()
    assert mapping.dest.model == a.name()
    assert mapping.src.var == forcing_var
    assert mapping.dest.var == a_input_var
    assert mapping.via == via
    assert not mapping.is_src_alias()
    assert not mapping.is_dest_alias()


def build_model(
    name: str, inputs: list[str | tuple[str, str]], outputs: list[str | tuple[str, str]]
) -> Model:
    inputs_bldr = InputsBuilder()
    for input_name in inputs:
        if isinstance(input_name, tuple):
            input_name, alias = input_name
            inputs_bldr.add_input(Var(name=input_name), alias)
        else:
            inputs_bldr.add_input(Var(name=input_name))

    outputs_bldr = OutputsBuilder()
    for output_name in outputs:
        if isinstance(output_name, tuple):
            output_name, alias = output_name
            outputs_bldr.add_output(Var(name=output_name), alias)
        else:
            outputs_bldr.add_output(Var(name=output_name))

    return Model(name=name, inputs=inputs_bldr.build(), outputs=outputs_bldr.build())


def mapping_into_src_via_dest(mapping: VarMapping) -> tuple[str, str, str]:
    return mapping.src.model, mapping.via, mapping.dest.model


VALIDATE_INPUT_MAPPING_CASES = [
    # case: select non-aliased
    (
        (
            # model name, inputs, outputs
            # tuple of inputs / outputs is name alias pair
            ("_", list(), [("a", "b")]),
            ("forcing", list(), ["a"]),
            ("model", ["a"], list()),
        ),
        {
            # src, via, dest
            ("forcing", "a", "model"),
        },
    ),
    # case: select non-aliased flip ordering
    (
        (
            ("forcing", list(), ["output"]),
            ("_", list(), [("output", "actual")]),
            ("model", ["output"], list()),
        ),
        {
            ("forcing", "output", "model"),
        },
    ),
    # case: select using alias
    (
        (
            ("_", list(), ["input"]),
            ("forcing", list(), ["output"]),
            ("model", [("input", "output")], list()),
        ),
        {
            ("forcing", "output", "model"),
        },
    ),
    # case: select using alias flip ordering
    (
        (
            ("forcing", list(), ["output"]),
            ("_", list(), ["input"]),
            ("model", [("input", "output")], list()),
        ),
        {
            ("forcing", "output", "model"),
        },
    ),
    # case: select first non-aliased if all aliased
    (
        (
            ("forcing", list(), [("output", "forcing_alias")]),
            ("_", list(), [("output", "a_alias")]),
            ("model", ["output"], list()),
        ),
        {
            ("forcing", "output", "model"),
        },
    ),
    # case: select non-aliased with alias present
    (
        (
            ("forcing", list(), [("a", "b")]),
            ("model", ["a"], list()),
        ),
        {
            ("forcing", "a", "model"),
        },
    ),
    # case: select non-aliased using aliased
    (
        (
            ("forcing", list(), ["output"]),
            ("_", list(), [("output", "actual")]),
            ("model", [("input", "output")], list()),
        ),
        {
            ("forcing", "output", "model"),
        },
    ),
    # case: multi-input
    (
        (
            ("forcing", list(), [("output", "output_alias")]),
            (
                "model",
                [
                    ("input", "output"),
                    ("input_2", "output"),
                    ("input_3", "output_alias"),
                ],
                list(),
            ),
        ),
        {
            ("forcing", "output", "model"),
            ("forcing", "output_alias", "model"),
        },
    ),
]


@pytest.mark.parametrize("mods, validation", VALIDATE_INPUT_MAPPING_CASES)
def test_validate_input_mapping_positive(
    mods: list[tuple[str, list[str | tuple[str, str]], list[str | tuple[str, str]]]],
    validation: set[tuple[str, str, str]],
):
    models: list[Model] = [
        build_model(name, inputs, outputs) for (name, inputs, outputs) in mods
    ]
    valid, unset = resolve_inputs_mapping(*models)
    assert len(valid) > 0
    assert len(unset) == 0
    for _, mappings in valid.items():
        for mapping in mappings:
            assert mapping_into_src_via_dest(mapping) in validation


VALIDATE_INPUT_MAPPING_CASES_NEGATIVE = [
    # case: no provider
    (
        (
            # model name, inputs, outputs
            # tuple of inputs / outputs is name alias pair
            ("forcing", list(), ["output"]),
            ("model", ["no_input"], list()),
        ),
        {
            # model, var or alias
            ("model", "no_input"),
        },
    ),
    # case: no provider b.c. invalid alias
    (
        (
            # model name, inputs, outputs
            # tuple of inputs / outputs is name alias pair
            ("forcing", list(), ["output"]),
            ("model", [("output", "no_input")], list()),
        ),
        {
            # model, var or alias
            ("model", "output"),
        },
    ),
]


@pytest.mark.parametrize("mods, validation", VALIDATE_INPUT_MAPPING_CASES_NEGATIVE)
def test_validate_input_mapping_negative(
    mods: list[tuple[str, list[str | tuple[str, str]], list[str | tuple[str, str]]]],
    validation: set[tuple[str, str, str]],
):
    models: list[Model] = [
        build_model(name, inputs, outputs) for (name, inputs, outputs) in mods
    ]
    _, unset = resolve_inputs_mapping(*models)
    assert len(unset) > 0

    for model, vars in unset.items():
        for var in vars:
            assert (model, var.name) in validation
