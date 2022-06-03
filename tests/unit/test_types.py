from typing import cast
from unittest import TestCase

# from openslides_backend.shared.exceptions import View400Exception
from openslides_backend.shared.patterns import (
    Collection,
    CollectionField,
    FullQualifiedField,
    FullQualifiedId,
    collection_from_fqid,
    fqid_from_fqfield,
    id_from_fqid,
)


class TypesTester(TestCase):
    """
    Tests some utils and types
    """

    def test_collection(self) -> None:
        collection = cast(Collection, "collection_vi8cah2Eih")
        self.assertEqual(str(collection), "collection_vi8cah2Eih")

    def test_collection_comparing(self) -> None:
        collection_1 = cast(Collection, "collection_aeboo3ieSh")
        collection_2 = "collection_aeboo3ieSh"
        self.assertEqual(collection_1, collection_2)

    def test_collection_hashing(self) -> None:
        collection = cast(Collection, "collection_inchosoo")
        self.assertEqual(hash(collection), hash("collection_inchosoo"))

    def test_full_qualified_id(self) -> None:
        fqid = cast(FullQualifiedId, "collection_aidahdoot/8283937728")
        self.assertEqual(str(fqid), "collection_aidahdoot/8283937728")

    def test_full_qualified_id_comparing(self) -> None:
        fqid_1 = cast(FullQualifiedId, "collection_reeyiewoo/2133862900")
        fqid_2 = "collection_reeyiewoo/2133862900"
        self.assertEqual(fqid_1, fqid_2)

    def test_full_qualified_id_hashing(self) -> None:
        fqid = cast(FullQualifiedId, "collection_iaoyuiso/9638688299")
        self.assertEqual(hash(fqid), hash("collection_iaoyuiso/9638688299"))

    def test_full_qualified_field(self) -> None:
        fqfield = cast(
            FullQualifiedField, "collection_hoouutu/7208641662/field_ais1aBau6d"
        )
        self.assertEqual(str(fqfield), "collection_hoouutu/7208641662/field_ais1aBau6d")

    def test_full_qualified_field_comparing(self) -> None:
        fqfield_1 = cast(
            FullQualifiedField, "collection_ioohcuiu/7208641662/field_epee2jeRee"
        )
        fqfield_2 = "collection_ioohcuiu/7208641662/field_epee2jeRee"
        self.assertEqual(fqfield_1, fqfield_2)

    def test_full_qualified_field_hashing(self) -> None:
        fqfield = cast(
            FullQualifiedField, "collection_ohfhooi/8432643375/field_Raechee5ee"
        )
        self.assertEqual(
            hash(fqfield), hash("collection_ohfhooi/8432643375/field_Raechee5ee")
        )

    def test_full_qualified_field_fqid(self) -> None:
        fqfield = cast(
            FullQualifiedField, "collection_quephaho/3148072663/field_Ein2Aos0Ku"
        )
        self.assertEqual(
            fqid_from_fqfield(fqfield),
            cast(FullQualifiedId, "collection_quephaho/3148072663"),
        )

    def test_collection_field(self) -> None:
        cf = cast(CollectionField, "collection/field")
        self.assertEqual(cf, "collection/field")

    def test_collection_field_comparing(self) -> None:
        cf_1 = cast(CollectionField, "collection/field")
        cf_2 = "collection/field"
        self.assertEqual(cf_1, cf_2)

    def test_collection_field_hashing(self) -> None:
        cf = cast(CollectionField, "collection/field")
        self.assertEqual(hash(cf), hash("collection/field"))

    def test_string_to_fqid_ok(self) -> None:
        fqid = cast(FullQualifiedId, "model/1")
        assert collection_from_fqid(fqid) == "model"
        assert id_from_fqid(fqid) == 1
