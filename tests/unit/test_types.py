from unittest import TestCase

from openslides_backend.shared.patterns import (
    Collection,
    FullQualifiedField,
    FullQualifiedId,
    string_to_fqid,
)


class TypesTester(TestCase):
    """
    Tests some utils and types
    """

    def test_collection(self) -> None:
        collection = Collection("collection_vi8cah2Eih")
        self.assertEqual(str(collection), "collection_vi8cah2Eih")

    def test_collection_repr(self) -> None:
        collection = Collection("collection_yag3Boaqui")
        self.assertEqual(repr(collection), "Collection('collection_yag3Boaqui')")

    def test_collection_comparing(self) -> None:
        collection_1 = Collection("collection_aeboo3ieSh")
        collection_2 = Collection("collection_aeboo3ieSh")
        self.assertEqual(collection_1, collection_2)

    def test_collection_hashing(self) -> None:
        collection = Collection("collection_Din9chosoo")
        self.assertEqual(hash(collection), hash("collection_Din9chosoo"))

    def test_full_qualified_id(self) -> None:
        fqid = FullQualifiedId(Collection("collection_Aid6ahdooT"), 8283937728)
        self.assertEqual(str(fqid), "collection_Aid6ahdooT/8283937728")

    def test_full_qualified_id_repr(self) -> None:
        fqid = FullQualifiedId(Collection("collection_oozaiX1pee"), 7099085886)
        self.assertEqual(
            repr(fqid), "FullQualifiedId('collection_oozaiX1pee/7099085886')"
        )

    def test_full_qualified_id_comparing(self) -> None:
        fqid_1 = FullQualifiedId(Collection("collection_reeyie3Woo"), 2133862900)
        fqid_2 = FullQualifiedId(Collection("collection_reeyie3Woo"), 2133862900)
        self.assertEqual(fqid_1, fqid_2)

    def test_full_qualified_id_hashing(self) -> None:
        fqid = FullQualifiedId(Collection("collection_ia5Ooyuiso"), 9638688299)
        self.assertEqual(hash(fqid), hash("collection_ia5Ooyuiso/9638688299"))

    def test_full_qualified_field(self) -> None:
        fqfield = FullQualifiedField(
            Collection("collection_Shoo1uut4u"), 7208641662, "field_ais1aBau6d"
        )
        self.assertEqual(
            str(fqfield), "collection_Shoo1uut4u/7208641662/field_ais1aBau6d"
        )

    def test_full_qualified_field_repr(self) -> None:
        fqfield = FullQualifiedField(
            Collection("collection_yaiS2uthi8"), 78718784720, "field_ueth3Rohv8"
        )
        self.assertEqual(
            repr(fqfield),
            "FullQualifiedField('collection_yaiS2uthi8/78718784720/field_ueth3Rohv8')",
        )

    def test_full_qualified_field_comparing(self) -> None:
        fqfield_1 = FullQualifiedField(
            Collection("collection_ioMohcui0u"), 7208641662, "field_epee2jeRee"
        )
        fqfield_2 = FullQualifiedField(
            Collection("collection_ioMohcui0u"), 7208641662, "field_epee2jeRee"
        )
        self.assertEqual(fqfield_1, fqfield_2)

    def test_full_qualified_field_hashing(self) -> None:
        fqfield = FullQualifiedField(
            Collection("collection_ohf3Thoo9i"), 8432643375, "field_Raechee5ee"
        )
        self.assertEqual(
            hash(fqfield), hash("collection_ohf3Thoo9i/8432643375/field_Raechee5ee")
        )

    def test_full_qualified_field_fqid(self) -> None:
        fqfield = FullQualifiedField(
            Collection("collection_quephah8Oo"), 3148072663, "field_Ein2Aos0Ku"
        )
        self.assertEqual(
            fqfield.fqid,
            FullQualifiedId(Collection("collection_quephah8Oo"), 3148072663),
        )

    def test_string_to_fqid(self) -> None:
        fqid_str = "model/1"
        fqid = string_to_fqid(fqid_str)
        assert fqid.collection == Collection("model")
        assert fqid.id == 1
