from datastore.migrations import BaseModelMigration
from datastore.shared.util import fqid_from_collection_and_id
from datastore.writer.core import BaseRequestEvent, RequestUpdateEvent

from ...shared.filters import FilterOperator


class Migration(BaseModelMigration):
    """
    This migration removes all remnants of the old structure level field in meeting users.
    """

    target_migration_index = 54

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        events: list[BaseRequestEvent] = []
        themes = list(
            self.reader.filter(
                "theme",
                FilterOperator("theme_for_organization_id", "=", 1),
                ["headbar", "primary_500"],
            ).values()
        )
        theme = themes[0]
        default_color = theme.get("headbar") or (
            self.darken_color(str(theme["primary_500"]))
            if theme.get("primary_500")
            else "#134768"
        )
        db_models = self.reader.get_all(
            "projector", ["chyron_background_color", "chyron_font_color"]
        )
        for id_, model in db_models.items():
            events.append(
                RequestUpdateEvent(
                    fqid_from_collection_and_id("projector", id_),
                    {
                        "chyron_background_color_2": (
                            default_color
                            if model.get("chyron_background_color") is None
                            or model.get("chyron_background_color")
                            == theme.get("primary_500")
                            else self.darken_color(
                                str(model["chyron_background_color"])
                            )
                        ),
                        "chyron_font_color_2": model.get("chyron_font_color"),
                    },
                )
            )
        return events

    def darken_color(self, color: str) -> str:
        "this mirrors the headbar color generation in the client"
        stripped = color.lstrip("#")
        rgb = tuple(int(stripped[i : i + 2], 16) for i in range(0, 6, 2))
        darker = tuple((val**2) // 255 for val in rgb)

        p = 25 / 100
        rgb1 = darker
        rgb2 = rgb
        rgb = tuple([int((rgb2[i] - rgb1[i]) * p + rgb1[i]) for i in range(3)])
        return "#" + "".join(f"{i:02x}" for i in rgb)
