from collections import defaultdict
from typing import cast

from openslides_backend.datastore.writer.core import (
    BaseRequestEvent,
    RequestCreateEvent,
    RequestUpdateEvent,
)
from openslides_backend.migrations import BaseModelMigration
from openslides_backend.services.datastore.interface import PartialModel
from openslides_backend.shared.patterns import (
    collection_from_fqid,
    fqid_from_collection_and_id,
    id_from_fqid,
)


class Migration(BaseModelMigration):
    """
    This migration splits the mediafile models meeting data into
    its own model called 'meeting_mediafile'.
    """

    target_migration_index = 55
    split_fields = [
        "is_public",
        "inherited_access_group_ids",
        "access_group_ids",
        "list_of_speakers_id",
        "projection_ids",
        "attachment_ids",
        "used_as_logo_projector_main_in_meeting_id",
        "used_as_logo_projector_header_in_meeting_id",
        "used_as_logo_web_header_in_meeting_id",
        "used_as_logo_pdf_header_l_in_meeting_id",
        "used_as_logo_pdf_header_r_in_meeting_id",
        "used_as_logo_pdf_footer_l_in_meeting_id",
        "used_as_logo_pdf_footer_r_in_meeting_id",
        "used_as_logo_pdf_ballot_paper_in_meeting_id",
        "used_as_font_regular_in_meeting_id",
        "used_as_font_italic_in_meeting_id",
        "used_as_font_bold_in_meeting_id",
        "used_as_font_bold_italic_in_meeting_id",
        "used_as_font_monospace_in_meeting_id",
        "used_as_font_chyron_speaker_name_in_meeting_id",
        "used_as_font_projector_h1_in_meeting_id",
        "used_as_font_projector_h2_in_meeting_id",
    ]

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        events: list[BaseRequestEvent] = []
        mediafiles = cast(
            dict[int, PartialModel],
            self.reader.get_all("mediafile", ["id", "owner_id", *self.split_fields]),
        )
        meeting_fqids_to_update: dict[str, list[int]] = defaultdict(list)
        for id_, mediafile in mediafiles.items():
            if collection_from_fqid(owner_id := mediafile.pop("owner_id")) == "meeting":
                meeting_fqids_to_update[owner_id].append(mediafile["id"])
                events.extend(
                    [
                        RequestCreateEvent(
                            fqid_from_collection_and_id("meeting_mediafile", id_),
                            {
                                **mediafile,
                                "meeting_id": id_from_fqid(owner_id),
                                "mediafile_id": id_,
                            },
                        ),
                        RequestUpdateEvent(
                            fqid_from_collection_and_id("mediafile", id_),
                            {
                                **{
                                    field: None
                                    for field in self.split_fields
                                    if field in mediafile
                                },
                                "meeting_mediafile_ids": [id_],
                            },
                        ),
                    ]
                )
            else:
                assert not any(
                    mediafile.get(field)
                    for field in self.split_fields
                    if field != "is_public"
                )
                events.extend(
                    [
                        RequestUpdateEvent(
                            fqid_from_collection_and_id("mediafile", id_),
                            {
                                field: None
                                for field in self.split_fields
                                if field in mediafile
                            },
                        )
                    ]
                )
        events.extend(
            [
                RequestUpdateEvent(
                    meeting_fqid, {"meeting_mediafile_ids": mediafile_ids}
                )
                for meeting_fqid, mediafile_ids in meeting_fqids_to_update.items()
            ]
        )
        for collection in ["list_of_speakers", "projection"]:
            models = cast(
                dict[int, PartialModel],
                self.reader.get_all(collection, ["id", "content_object_id"]),
            )
            for id_, model in models.items():
                if (
                    collection_from_fqid(fqid := model["content_object_id"])
                    == "mediafile"
                ):
                    events.append(
                        RequestUpdateEvent(
                            fqid_from_collection_and_id(collection, id_),
                            {"content_object_id": "meeting_" + fqid},
                        )
                    )
        for collection in ["topic", "motion", "assignment"]:
            models = cast(
                dict[int, PartialModel],
                self.reader.get_all(collection, ["id", "attachment_ids"]),
            )
            events.extend(
                [
                    RequestUpdateEvent(
                        fqid_from_collection_and_id(collection, id_),
                        {
                            "attachment_meeting_mediafile_ids": model["attachment_ids"],
                            "attachment_ids": None,
                        },
                    )
                    for id_, model in models.items()
                    if "attachment_ids" in model
                ]
            )
        return events
