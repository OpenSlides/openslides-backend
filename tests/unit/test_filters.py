from openslides_backend.shared.filters import And, FilterOperator, Not, Or


def test_filter_operator() -> None:
    filter = FilterOperator("f", "=", 1)
    assert filter.to_dict() == {
        "field": "f",
        "operator": "=",
        "value": 1,
    }


def test_not_operator() -> None:
    filter = FilterOperator("f", "=", 1)
    not_ = Not(filter)
    assert not_.to_dict() == {"not_filter": filter.to_dict()}


def test_and_operator() -> None:
    filter1 = FilterOperator("f", "=", 1)
    filter2 = FilterOperator("f", "<", 2)
    and_ = And(filter1, filter2)
    assert and_.to_dict() == {"and_filter": [filter1.to_dict(), filter2.to_dict()]}


def test_or_operator() -> None:
    filter1 = FilterOperator("f", "=", 1)
    filter2 = FilterOperator("f", "<", 2)
    or_ = Or(filter1, filter2)
    assert or_.to_dict() == {"or_filter": [filter1.to_dict(), filter2.to_dict()]}


def test_complex_operator() -> None:
    filter1 = FilterOperator("f", "=", 1)
    filter2 = FilterOperator("f", "<", 2)
    not_ = Not(filter2)
    or_ = Or(filter1, not_)
    assert or_.to_dict() == {"or_filter": [filter1.to_dict(), not_.to_dict()]}
