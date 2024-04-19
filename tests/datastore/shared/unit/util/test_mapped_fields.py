from openslides_backend.datastore.reader.core import GetManyRequest, GetManyRequestPart


def test_correct():
    request = GetManyRequest([GetManyRequestPart("test", [1], ["f"])])
    mapped_fields = request.build_mapped_fields()
    assert not mapped_fields.needs_whole_model
    assert mapped_fields.fqids == ["test/1"]
    assert mapped_fields.collections == ["test"]
    assert mapped_fields.unique_fields == ["f"]
    assert mapped_fields.per_fqid["test/1"] == ["f"]


def test_correct_empty_mapped_fields():
    request = GetManyRequest([GetManyRequestPart("test", [1], [])])
    mapped_fields = request.build_mapped_fields()
    assert mapped_fields.needs_whole_model


def test_correct_too_many_fields():
    fields = [f"f{i}" for i in range(1500)]
    request = GetManyRequest([GetManyRequestPart("test", [1], fields)])
    mapped_fields = request.build_mapped_fields()
    assert mapped_fields.needs_whole_model
