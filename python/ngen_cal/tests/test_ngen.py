import pytest
from ngen.cal.ngen import NgenExplicit, NgenIndependent, NgenUniform, NgenStrategy


def test_NgenExplicit_strategy_default_value():
    # construct object without validation.
    o = NgenExplicit.construct()
    assert o.strategy == NgenStrategy.explicit


def test_NgenIndependent_strategy_default_value():
    # construct object without validation.
    o = NgenIndependent.construct()
    assert o.strategy == NgenStrategy.independent

def test_NgenUniform_strategy_default_value():
    # construct object without validation.
    o = NgenUniform.construct()
    assert o.strategy == NgenStrategy.uniform
