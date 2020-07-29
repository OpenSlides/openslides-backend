from openslides_backend.shared.filters import And, FilterOperator, Not, Or


def test_FilterOperator() -> None:
    field = "f"
    value = "1"
    operator = "="
    filter = FilterOperator(field, operator, value)
    assert filter.to_dict() == {
        "field": field,
        "value": value,
        "operator": operator,
    }


def test_NotOperator() -> None:
    field = "f"
    value = "1"
    operator = "="
    filter = FilterOperator(field, operator, value)
    not_ = Not(filter)
    assert not_.to_dict() == {"not_filter": filter.to_dict()}


def test_AndOperator() -> None:
    field1 = "f"
    value1 = "1"
    operator1 = "="
    filter1 = FilterOperator(field1, operator1, value1)
    field2 = "f"
    value2 = "2"
    operator2 = "<"
    filter2 = FilterOperator(field2, operator2, value2)
    and_ = And(filter1, filter2)
    assert and_.to_dict() == {"and_filter": [filter1.to_dict(), filter2.to_dict()]}


def test_OrOperator() -> None:
    field1 = "f"
    value1 = "1"
    operator1 = "="
    filter1 = FilterOperator(field1, operator1, value1)
    field2 = "f"
    value2 = "2"
    operator2 = "<"
    filter2 = FilterOperator(field2, operator2, value2)
    or_ = Or(filter1, filter2)
    assert or_.to_dict() == {"or_filter": [filter1.to_dict(), filter2.to_dict()]}


def test_ComplexOperator() -> None:
    field1 = "f"
    value1 = "1"
    operator1 = "="
    filter1 = FilterOperator(field1, operator1, value1)
    field2 = "f"
    value2 = "2"
    operator2 = "<"
    filter2 = FilterOperator(field2, operator2, value2)
    not_ = Not(filter2)
    or_ = Or(filter1, not_)
    assert or_.to_dict() == {"or_filter": [filter1.to_dict(), not_.to_dict()]}
