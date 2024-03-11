#!/usr/bin/env python
from sync_app.parsers.python_filter import PythonFilter
from sync_app.exceptions import InvalidSCIMFilter
from abnf.parser import NodeVisitor
from sync_app.parsers.scim_query_filter import Rule as SCIMQueryRule
import pytest


def test_username_query():
    predicate = PythonFilter.parse_filter_to_predicate('userName eq "bjensen"')
    assert predicate({"userName": "bjensen"})
    assert not predicate({"userName": "b"})
    assert not predicate({"userName": "bjensen "})
    assert not predicate({"userName": " bjensen"})
    assert not predicate({"userName": " bjensen"})


def test_attribute_query():
    predicate = PythonFilter.parse_filter_to_predicate("userName pr")
    assert predicate({"userName": "bjensen"})
    assert not predicate({"userName": ""})
    assert not predicate({"userName": False})
    assert not predicate({"test": "bjensen"})
    assert not predicate({"parent": {"userName": "test"}})


def test_attribute_query_case_sensitive():
    predicate = PythonFilter.parse_filter_to_predicate("userName pr")
    assert predicate({"userName": {"userName": "test"}})
    assert not predicate({"username": {"userName": "test"}})


def test_not_prefix():
    predicate = PythonFilter.parse_filter_to_predicate("not ( userName pr )")
    assert not predicate({"userName": {"userName": "test"}})
    assert predicate({})
    assert predicate({"userFame": "super"})


def test_double_not_prefix():
    predicate = PythonFilter.parse_filter_to_predicate("not (not ( userName pr ))")
    assert predicate({"userName": {"userName": "test"}})
    assert not predicate({})
    assert not predicate({"userFame": "super"})


def test_comparison_string_le():
    predicate = PythonFilter.parse_filter_to_predicate('userName le "claire"')
    assert predicate({"userName": "aaron"})
    assert predicate({"userName": "c"})
    assert not predicate({})
    assert not predicate({"userName": "tyler"})


def test_comparison_string_gt():
    predicate = PythonFilter.parse_filter_to_predicate('userName gt "claire"')
    assert not predicate({"userName": "aaron"})
    assert not predicate({})
    assert predicate({"userName": "tyler"})


def test_comparison_string_lt():
    predicate = PythonFilter.parse_filter_to_predicate('userName lt "claire"')
    assert not predicate({"userName": "claire"})
    assert not predicate({})
    assert not predicate({"userName": "tyler"})
    assert predicate({"userName": "aaron"})


def test_comparison_string_ge():
    predicate = PythonFilter.parse_filter_to_predicate('userName ge "claire"')
    assert predicate({"userName": "claire"})
    assert not predicate({})
    assert predicate({"userName": "tyler"})
    assert not predicate({"userName": "aaron"})


def test_comparison_string_ew():
    predicate = PythonFilter.parse_filter_to_predicate('userName ew "claire"')
    assert predicate({"userName": "eclaire"})
    assert not predicate({"userName": "are"})


def test_comparison_string_sw():
    predicate = PythonFilter.parse_filter_to_predicate('userName sw "claire"')
    assert predicate({"userName": "claireese"})
    assert not predicate({"userName": "laire"})
    assert not predicate({"userName": "clair"})
    assert not predicate({"userName": ""})


def test_comparison_string_co():
    predicate = PythonFilter.parse_filter_to_predicate('userName co "la"')
    assert predicate({"userName": "claireese"})
    assert predicate({"userName": "laire"})
    assert predicate({"userName": "clair"})
    assert not predicate({"userName": ""})
    assert not predicate({"userName": "al"})


def test_comparison_string_ne():
    predicate = PythonFilter.parse_filter_to_predicate('userName ne "claire"')
    assert predicate({"userName": "claireese"})
    assert predicate({"userName": "laire"})
    assert predicate({"userName": "clair"})
    assert not predicate({"userName": "claire"})


def test_comparison_string_eq():
    predicate = PythonFilter.parse_filter_to_predicate('userName eq "claire"')
    assert not predicate({"userName": "claireese"})
    assert not predicate({"userName": "laire"})
    assert not predicate({"userName": "clair"})
    assert predicate({"userName": "claire"})


def test_comparison_number_le():
    predicate = PythonFilter.parse_filter_to_predicate("userName le 5")
    assert predicate({"userName": 5})
    assert predicate({"userName": 1})
    assert predicate({"userName": 1.0})
    assert not predicate({"userName": 6.0})
    with pytest.raises(InvalidSCIMFilter):
        assert not predicate({"userName": "aaron"})
    assert not predicate({})


def test_comparison_number_ge():
    predicate = PythonFilter.parse_filter_to_predicate("userName ge 5")
    assert predicate({"userName": 5})
    assert not predicate({"userName": 1})
    assert not predicate({"userName": 1.0})
    assert predicate({"userName": 6.0})
    with pytest.raises(InvalidSCIMFilter):
        assert not predicate({"userName": "aaron"})
    assert not predicate({})


def test_comparison_number_lt():
    predicate = PythonFilter.parse_filter_to_predicate("userName lt 5")
    assert not predicate({"userName": 5})
    assert predicate({"userName": 1})
    assert predicate({"userName": 1.0})
    assert not predicate({"userName": 6.0})
    with pytest.raises(InvalidSCIMFilter):
        assert not predicate({"userName": "aaron"})
    assert not predicate({})


def test_comparison_number_gt():
    predicate = PythonFilter.parse_filter_to_predicate("userName gt 5")
    assert not predicate({"userName": 5})
    assert not predicate({"userName": 1})
    assert not predicate({"userName": 1.0})
    assert predicate({"userName": 6.0})
    with pytest.raises(InvalidSCIMFilter):
        assert not predicate({"userName": "aaron"})


def test_comparison_number_ew():
    predicate = PythonFilter.parse_filter_to_predicate("userName ew 5")
    assert not predicate({"userName": 5})
    assert not predicate({"userName": 1})
    assert not predicate({"userName": 1.0})
    assert not predicate({"userName": 6.0})
    with pytest.raises(InvalidSCIMFilter):
        assert not predicate({"userName": "aaron"})


def test_comparison_number_sw():
    predicate = PythonFilter.parse_filter_to_predicate("userName sw 5")
    assert not predicate({"userName": 5})
    assert not predicate({"userName": 1})
    assert not predicate({"userName": 1.0})
    assert not predicate({"userName": 6.0})
    with pytest.raises(InvalidSCIMFilter):
        assert not predicate({"userName": "aaron"})


def test_comparison_number_co():
    predicate = PythonFilter.parse_filter_to_predicate("userName co 5")
    assert not predicate({"userName": 5})
    assert not predicate({"userName": 1})
    assert not predicate({"userName": 1.0})
    assert not predicate({"userName": 6.0})
    with pytest.raises(InvalidSCIMFilter):
        assert not predicate({"userName": "aaron"})


def test_comparison_number_ne():
    predicate = PythonFilter.parse_filter_to_predicate("userName ne 5")
    assert not predicate({"userName": 5})
    assert not predicate({"userName": 5.0})
    assert predicate({"userName": 1})
    assert predicate({"userName": 1.0})
    assert predicate({"userName": 6.0})
    assert predicate({"userName": "aaron"})
    assert predicate({})


def test_comparison_number_eq():
    predicate = PythonFilter.parse_filter_to_predicate("userName eq 5")
    assert predicate({"userName": 5})
    assert predicate({"userName": 5.0})
    assert not predicate({"userName": 1})
    assert not predicate({"userName": 1.0})
    assert not predicate({"userName": 6.0})
    assert not predicate({"userName": "aaron"})
    assert not predicate({})
    assert not predicate({})


def test_attribute_name_complex():
    predicate = PythonFilter.parse_filter_to_predicate("a1-steak_sauce pr")
    assert predicate({"a1-steak_sauce": True})


def test_attribute_path_complex():
    predicate = PythonFilter.parse_filter_to_predicate(
        "a1-steak_sauce.important eq true"
    )
    assert predicate({"a1-steak_sauce": {"important": True}})


def test_subattribute_query():
    predicate = PythonFilter.parse_filter_to_predicate('name[givenName eq "mark"]')
    assert predicate({"name": {"givenName": "mark"}})
    assert not predicate({"name": {"givenName": "tom"}})


def test_nested_subattribute_query():
    predicate = PythonFilter.parse_filter_to_predicate("car.model[year eq 1997]")
    assert predicate({"car": {"model": {"year": 1997}}})
    assert not predicate({"car": {"model": {"year": 1998}}})
