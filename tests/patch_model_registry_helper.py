from unittest.mock import _patch, patch

from openslides_backend.models.base import Model, ModelMetaClass
from openslides_backend.models.fields import Field
from openslides_backend.shared.patterns import Collection

fake_registry: dict[Collection, type["Model"]] = {}


class FakeModelMetaClass(ModelMetaClass):
    """
    Metaclass for generic test models.
    Registers each `FakeModel` subclass in `fake_registry` instead of
    the global `model_registry`.
    """

    def __new__(metaclass, class_name, class_parents, class_attributes):  # type: ignore
        new_class = type.__new__(metaclass, class_name, class_parents, class_attributes)

        if class_name not in ["FakeModel"]:
            for attr_name in class_attributes:
                attr = getattr(new_class, attr_name)
                if isinstance(attr, Field):
                    attr.own_collection = new_class.collection
                    attr.own_field_name = attr_name
            fake_registry[new_class.collection] = new_class
        return new_class


class FakeModel(Model, metaclass=FakeModelMetaClass):
    """
    Custom Model class used to define generic test models.
    Its instances behave like regular `Model` objects but are
    intentionally not included in the global `model_registry`.
    """

    collection: Collection
    verbose_name: str


class PatchModelRegistryMixin:
    """
    Mixin that replaces `model_registry` in selected backend modules with a
    custom (fake) registry, allowing tests to run with models that are not
    defined in `models.yml`.

    Override the following class attributes as needed:

    * fake_model_registry
      The registry object to patch in. Defaults to all `FakeModel` instances
      defined in the backend.

    * patch_targets
      List of module paths whose `model_registry` attribute will be patched.

    * init_with_login
      Whether tests should run with login initialization enabled. Defaults to
      False. If set to True, ensure that `fake_model_registry` includes all
      real models required by the login process.
    """

    fake_model_registry: dict[Collection, type["Model"]] = fake_registry
    patch_targets: list[str] = [
        "openslides_backend.action.action",
        "openslides_backend.action.relations.single_relation_handler",
        "openslides_backend.services.database.database_writer",
        "tests.system.base",
    ]
    init_with_login: bool = False

    patchers: list[_patch]

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()  # type: ignore

        cls.patchers = []
        for target in cls.patch_targets:
            p = patch(f"{target}.model_registry", cls.fake_model_registry)
            p.start()
            cls.patchers.append(p)

    @classmethod
    def tearDownClass(cls) -> None:
        for p in cls.patchers:
            p.stop()
        super().tearDownClass()  # type: ignore
