from typing import Any, Literal

from openslides_backend.action.actions.speaker.speech_state import SpeechState
from openslides_backend.services.datastore.with_database_context import (
    with_database_context,
)
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID, ONE_ORGANIZATION_ID
from tests.system.action.base import BaseActionTestCase

# begin_time, end_time, total_pause, speech_state, answer, note, point_of_order, meeting_user_id
SpeakerData = tuple[
    int | None,
    int | None,
    int | None,
    SpeechState | None,
    bool | None,
    str | None,
    bool | None,
    int,
]

# structure_level_id, initial_time, additional_time, remaining_time, speaker_ids
SLLOSData = tuple[int, int, int | None, int, list[int]]

FileEndString = Literal["png", "txt", "pdf"]

EXAMPLE_LOS_DATA: list[list[SpeakerData]] = [
    [
        (100, 200, None, SpeechState.PRO, None, None, False, 4),
        (
            200,
            300,
            50,
            None,
            None,
            "This is a finished point of order, so it's okay.",
            True,
            5,
        ),
        (300, 400, None, SpeechState.INTERVENTION, None, None, None, 6),
        (None, None, None, SpeechState.INTERVENTION, True, None, None, 4),
    ],
    [
        (400, 600, 100, None, None, None, None, 7),
        (600, 700, 50, SpeechState.INTERPOSED_QUESTION, False, None, None, 8),
        (
            625,
            675,
            None,
            SpeechState.INTERPOSED_QUESTION,
            True,
            None,
            None,
            7,
        ),
        (
            700,
            800,
            None,
            None,
            None,
            "Another finished point of order. With a category.",
            True,
            9,
        ),
        (
            800,
            900,
            None,
            None,
            None,
            "Yet another finished point of order. With a category.",
            True,
            4,
        ),
    ],
    [
        (None, None, None, None, None, None, None, 1),  # 10
        (None, None, None, None, None, None, None, 4),  # 11
        (None, None, None, None, None, None, None, 5),  # 12
        (None, None, None, None, None, None, None, 6),  # 13
        (None, None, None, None, None, None, None, 7),  # 14
        (None, None, None, None, None, None, None, 8),  # 15
        (None, None, None, None, None, None, None, 9),  # 16
        (None, None, None, None, None, None, None, 11),  # 17
        (None, None, None, None, None, None, None, 13),  # 18
        (None, None, None, None, None, None, None, 16),  # 19
    ],
    [
        (
            900,
            1000,
            None,
            None,
            None,
            "These are all with a category btw",
            True,
            11,
        ),  # 20
        (1000, 1100, None, None, None, None, True, 13),  # 21
        (1100, 1200, None, None, None, None, True, 16),  # 22
    ],
    [
        (1200, 1300, None, SpeechState.CONTRIBUTION, None, None, None, 4),  # 23
        (1300, 1400, None, None, None, None, None, 5),  # 24
        (1400, 1500, 50, None, None, None, None, 6),  # 25
        (1500, 1600, None, None, None, None, None, 7),  # 26
        (None, None, None, None, None, None, None, 8),  # 27
        (None, None, None, None, None, None, None, 9),  # 28
    ],
]

EXAMPLE_SLLOS_DATA: list[list[SLLOSData]] = [
    [
        (1, 600, None, 600, [10]),
        (2, 600, None, 600, [12]),
        (3, 600, None, 600, [13]),
        (4, 600, None, 600, [11, 16, 18, 19]),
        (5, 600, None, 600, [14]),
        (6, 600, None, 600, [15]),
        (7, 600, None, 600, [17]),
    ],
    [
        (1, 600, 50, 500, [20]),
        (10, 600, 50, 500, [21]),
    ],
    [
        (8, 600, None, 400, [23, 24]),
        (9, 600, None, 550, [25]),
        (10, 600, None, 500, [26]),
        (11, 600, None, 600, [27]),
        (12, 600, None, 600, [28]),
    ],
]


class AgendaItemForwardActionTest(BaseActionTestCase):
    @with_database_context
    def create_topic_agenda_item(
        self,
        agenda_item_id: int = 1,
        topic_id: int = 10,
        meeting_id: int = 1,
        parent_id: int | None = None,
        extra_agenda_fields: dict[str, Any] = {},
        extra_los_fields: dict[str, Any] = {},
    ) -> None:
        """
        Creates an agenda_item linked to a topic.
        The list_of_speakers for the topic will have the id topic_id * 10.
        """
        meeting = self.datastore.get(
            f"meeting/{meeting_id}",
            ["agenda_item_ids", "topic_ids", "list_of_speakers_ids"],
            lock_result=False,
        )
        self.set_models(
            {
                f"meeting/{meeting_id}": {
                    "agenda_item_ids": [
                        *meeting.get("agenda_item_ids", []),
                        agenda_item_id,
                    ],
                    "topic_ids": [*meeting.get("topic_ids", []), topic_id],
                    "list_of_speakers_ids": [
                        *meeting.get("list_of_speakers_ids", []),
                        topic_id * 10,
                    ],
                },
                f"agenda_item/{agenda_item_id}": {
                    "content_object_id": f"topic/{topic_id}",
                    "meeting_id": meeting_id,
                    "weight": agenda_item_id,
                    **extra_agenda_fields,
                },
                f"topic/{topic_id}": {
                    "agenda_item_id": agenda_item_id,
                    "list_of_speakers_id": topic_id * 10,
                    "meeting_id": meeting_id,
                    "title": f"Topic {topic_id}",
                    "text": f"This is the text of topic {topic_id}",
                    "sequential_number": topic_id,
                },
                f"list_of_speakers/{topic_id*10}": {
                    "content_object_id": f"topic/{topic_id}",
                    "meeting_id": meeting_id,
                    "sequential_number": topic_id * 10,
                    **extra_los_fields,
                },
            }
        )
        if parent_id:
            parent = self.datastore.get(
                f"agenda_item/{parent_id}", ["child_ids"], lock_result=False
            )
            self.set_models(
                {
                    f"agenda_item/{agenda_item_id}": {"parent_id": parent_id},
                    f"agenda_item/{parent_id}": {
                        "child_ids": [*parent.get("child_ids", []), agenda_item_id],
                    },
                }
            )

    @with_database_context
    def create_speakers_for_los(
        self,
        meeting_id: int = 1,
        los_id: int = 1,
        base_speaker_id: int = 1,
        speaker_data: list[SpeakerData] = [],
    ) -> None:
        all_speaker_ids = [
            *self.datastore.get(f"meeting/{meeting_id}", ["speaker_ids"]).get(
                "speaker_ids", []
            ),
            *range(base_speaker_id, base_speaker_id + len(speaker_data)),
        ]
        self.set_models(
            {
                f"meeting/{meeting_id}": {"speaker_ids": all_speaker_ids},
                f"list_of_speakers/{los_id}": {
                    "speaker_ids": list(
                        range(base_speaker_id, base_speaker_id + len(speaker_data))
                    )
                },
                **{
                    f"speaker/{base_speaker_id+i}": {
                        "meeting_id": meeting_id,
                        "list_of_speakers_id": los_id,
                        "meeting_user_id": date[7],
                        "weight": i,
                        **{
                            field: val
                            for j, field in enumerate(
                                [
                                    "begin_time",
                                    "end_time",
                                    "total_pause",
                                    "speech_state",
                                    "answer",
                                    "note",
                                    "point_of_order",
                                ]
                            )
                            if (val := date[j]) is not None
                        },
                    }
                    for i, date in enumerate(speaker_data)
                },
            }
        )

    def create_structure_levels(
        self, levels: dict[str, str | None], base_level_id: int = 1, meeting_id: int = 1
    ) -> None:
        self.set_models(
            {
                f"meeting/{meeting_id}": {
                    "structure_level_ids": list(
                        range(base_level_id, base_level_id + len(levels))
                    )
                },
                **{
                    f"structure_level/{id_}": {
                        "meeting_id": meeting_id,
                        "name": item[0],
                        **({"color": item[1]} if item[1] else {}),
                    }
                    for id_, item in enumerate(levels.items(), base_level_id)
                },
            }
        )

    def add_structure_levels_to_meeting_users(
        self, mu_to_sl_ids: dict[int, list[int]]
    ) -> None:
        sl_to_mu_ids: dict[int, list[int]] = {}
        for mu_id, sl_ids in mu_to_sl_ids.items():
            for sl_id in sl_ids:
                if sl_id not in sl_to_mu_ids:
                    sl_to_mu_ids[sl_id] = [mu_id]
                else:
                    sl_to_mu_ids[sl_id].append(mu_id)
        self.set_models(
            {
                **{
                    f"meeting_user/{mu_id}": {"structure_level_ids": sl_ids}
                    for mu_id, sl_ids in mu_to_sl_ids.items()
                },
                **{
                    f"structure_level/{sl_id}": {"meeting_user_ids": sorted(mu_ids)}
                    for sl_id, mu_ids in sl_to_mu_ids.items()
                },
            }
        )

    def create_sllos(
        self,
        los_id_to_sllos_data: dict[int, list[SLLOSData]],
        meeting_id: int = 1,
        base_sllos_id: int = 1,
    ) -> None:
        next_sllos_id = base_sllos_id
        speaker_to_sllos_id: dict[int, int] = {}
        data: dict[str, dict[str, Any]] = {}
        for los_id, sllos_data in los_id_to_sllos_data.items():
            data[f"list_of_speakers/{los_id}"] = {
                "structure_level_list_of_speakers_ids": list(
                    range(next_sllos_id, next_sllos_id + len(sllos_data))
                )
            }
            for sllos_date in sllos_data:
                (
                    structure_level_id,
                    initial_time,
                    additional_time,
                    remaining_time,
                    speaker_ids,
                ) = sllos_date
                speaker_to_sllos_id.update(
                    {speaker_id: next_sllos_id for speaker_id in speaker_ids}
                )
                data[f"structure_level_list_of_speakers/{next_sllos_id}"] = {
                    "meeting_id": meeting_id,
                    "list_of_speakers_id": los_id,
                    "structure_level_id": structure_level_id,
                    "initial_time": initial_time,
                    "remaining_time": remaining_time,
                    "speaker_ids": speaker_ids,
                }
                if additional_time:
                    data[f"structure_level_list_of_speakers/{next_sllos_id}"][
                        "additional_time"
                    ] = additional_time
                next_sllos_id += 1
        self.set_models(
            {
                f"meeting/{meeting_id}": {
                    "structure_level_list_of_speakers_ids": list(
                        range(base_sllos_id, next_sllos_id)
                    )
                },
                **data,
                **{
                    f"speaker/{speaker_id}": {
                        "structure_level_list_of_speakers_id": sllos_id
                    }
                    for speaker_id, sllos_id in speaker_to_sllos_id.items()
                },
            }
        )

    def create_poocs(
        self,
        meeting_id_to_pooc_id_to_data: dict[int, dict[int, tuple[str, int, list[int]]]],
    ) -> None:
        self.set_models(
            {
                **{
                    f"meeting/{meeting_id}": {
                        "point_of_order_category_ids": list(pooc_ids)
                    }
                    for meeting_id, pooc_ids in meeting_id_to_pooc_id_to_data.items()
                },
                **{
                    f"speaker/{speaker_id}": {"point_of_order_category_id": pooc_id}
                    for pooc_to_data in meeting_id_to_pooc_id_to_data.values()
                    for pooc_id, data in pooc_to_data.items()
                    for speaker_id in data[2]
                },
                **{
                    f"point_of_order_category/{pooc_id}": {
                        "meeting_id": meeting_id,
                        "text": data[0],
                        "rank": data[1],
                        "speaker_ids": data[2],
                    }
                    for meeting_id, pooc_to_data in meeting_id_to_pooc_id_to_data.items()
                    for pooc_id, data in pooc_to_data.items()
                },
            }
        )

    def add_meeting_mediafiles_to_topics(
        self, tp_to_mm_ids: dict[int, list[int]]
    ) -> None:
        mm_to_tp_ids: dict[int, list[int]] = {}
        for tp_id, mm_ids in tp_to_mm_ids.items():
            for mm_id in mm_ids:
                if mm_id not in mm_to_tp_ids:
                    mm_to_tp_ids[mm_id] = [tp_id]
                else:
                    mm_to_tp_ids[mm_id].append(tp_id)
        self.set_models(
            {
                **{
                    f"topic/{tp_id}": {"attachment_meeting_mediafile_ids": mm_ids}
                    for tp_id, mm_ids in tp_to_mm_ids.items()
                },
                **{
                    f"meeting_mediafile/{mm_id}": {
                        "attachment_ids": [f"topic/{tp_id}" for tp_id in sorted(tp_ids)]
                    }
                    for mm_id, tp_ids in mm_to_tp_ids.items()
                },
            }
        )

    def get_mediafile_data(
        self, name: str, filetype: FileEndString | None = None
    ) -> dict[str, Any]:
        title = f"{name}.{filetype}" if filetype else name
        data: dict[str, Any] = {
            "title": title,
        }
        if filetype:
            data["filename"] = title
            data["mimetype"] = (
                "text/plain"
                if filetype == "txt"
                else "image/png" if filetype == "png" else "application/png"
            )
            if filetype == "pdf":
                data["pdf_information"] = {"pages": 1}
        else:
            data["is_directory"] = True
        return data

    def create_full_dataset(
        self, with_mediafiles: bool = True, with_los_related_data: bool = True
    ) -> None:
        self.create_meeting()
        self.create_meeting(4)
        self.create_meeting(7)
        self.create_topic_agenda_item(
            1,
            11,
            extra_los_fields={
                "closed": True,
                "moderator_notes": "This is a short mod note.",
            },
        )
        self.create_topic_agenda_item(
            2,
            22,
            parent_id=1,
            extra_agenda_fields={
                "item_number": "TOP 2",
                "comment": "This is a comment.",
                "closed": True,
                "type": "internal",
                "duration": 600,
                "is_internal": True,
            },
            extra_los_fields={"moderator_notes": "This is a slightly longer mod note."},
        )
        self.create_topic_agenda_item(3, 33, parent_id=1)
        self.create_topic_agenda_item(
            4, 44, parent_id=2, extra_agenda_fields={"is_internal": True}
        )
        self.create_topic_agenda_item(
            5, 55, parent_id=2, extra_agenda_fields={"is_internal": True}
        )
        self.create_topic_agenda_item(
            6,
            66,
            extra_agenda_fields={
                "comment": "This one is hidden.",
                "type": "hidden",
                "is_internal": False,
            },
            extra_los_fields={"closed": True},
        )
        # Agenda in meeting 7 to check if the new items are sorted below
        self.create_topic_agenda_item(7, 77, meeting_id=7)
        self.set_models(
            {
                "agenda_item/1": {"tag_ids": [1, 2]},
                "committee/60": {"forward_agenda_to_committee_ids": [63, 66]},
                "committee/63": {"receive_agenda_forwardings_from_committee_ids": [60]},
                "committee/67": {"receive_agenda_forwardings_from_committee_ids": [60]},
                "group/1": {"name": "Default"},
                "group/2": {"name": "Admin"},
                "group/3": {"name": "Delegate"},
                "group/4": {"name": "Default"},
                "group/5": {"name": "Admin"},
                "group/6": {"name": "Gremlins"},
                "group/7": {"name": "Cherries"},
                "group/8": {"name": "Apples"},
                "group/9": {"name": "Bananas"},
                "tag/1": {
                    "meeting_id": 1,
                    "tagged_ids": ["agenda_item/1"],
                    "name": "Guten tag",
                },
                "tag/2": {
                    "meeting_id": 1,
                    "tagged_ids": ["agenda_item/1"],
                    "name": "Tag auch",
                },
            }
        )
        if with_los_related_data:
            self.set_user_groups(1, [2, 4, 8, 9])  # 1, musers: 1,2,3
            self.create_user("bob", [1])  # 2, musers: 4
            self.create_user("colin", [2])  # 3, musers: 5
            self.create_user("dan", [3])  # 4, musers: 6
            self.create_user("ekaterina", [1, 2])  # 5, musers: 7
            self.create_user("finn", [2, 3])  # 6, musers: 8
            self.create_user("gundula", [3, 4])  # 7, musers: 9,10
            self.create_user("haley", [2, 5])  # 8, musers: 11,12
            self.create_user("isabella", [3, 6, 9])  # 9, musers: 13,14,15
            self.create_user("john", [1, 2, 4])  # 10, musers: 16,17
            self.set_models(
                {
                    f"meeting_user/{id_}": {
                        field: val
                        for field, val in [
                            ("number", f"MTNGUSR{id_}"),
                            ("comment", f"Comment of meeting user{id_}"),
                            ("about_me", f"I am meeting user {id_}"),
                        ]
                        if len(field) - 6 != id_ % 3
                    }
                    for id_ in range(1, 18)
                }
            )
            self.create_structure_levels(
                {
                    "red": "#ff0000",
                    "orange": "#ff8000",
                    "yellow": "#ffff00",
                    "green": "#00ff00",
                    "cyan": "#00ffff",
                    "blue": "#0000ff",
                    "pink": "#ff00ff",
                    "purple": "#8000ff",
                    "white": "#ffffff",
                    "grey": "#808080",
                    "black": "#000000",
                    "nothing": None,
                },
                base_level_id=1,
                meeting_id=1,
            )
            self.create_structure_levels(
                {
                    "red": None,
                    "orange": "#ff8000",
                    "green": "#00ff33",
                    "ocean": "#0000ff",
                    "whitecat": "#ffffff",
                    "greycat": "#808080",
                    "blackcat": "#000000",
                    "void": None,
                },
                base_level_id=13,
                meeting_id=4,
            )
            self.add_structure_levels_to_meeting_users(
                mu_to_sl_ids={
                    2: [17],  # meeting 4
                    4: [1],
                    5: [2],
                    6: [3],
                    7: [12],
                    8: [2, 4, 6, 8, 10, 12],
                    9: [1, 3, 5, 7, 9, 11],
                    10: [13, 14, 15],  # meeting 4
                    11: [],
                    12: [16, 17, 18, 19, 20],  # meeting 4
                    13: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                    14: [],  # meeting 4
                    16: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                    17: [14, 16, 18, 20],  # meeting 4
                }
            )
            self.create_speakers_for_los(
                los_id=110,
                base_speaker_id=1,
                speaker_data=EXAMPLE_LOS_DATA[0],
            )
            self.create_speakers_for_los(
                los_id=220,
                base_speaker_id=5,
                speaker_data=EXAMPLE_LOS_DATA[1],
            )
            self.create_speakers_for_los(
                los_id=330,
                base_speaker_id=10,
                speaker_data=EXAMPLE_LOS_DATA[2],
            )
            self.create_speakers_for_los(
                los_id=440,
                base_speaker_id=20,
                speaker_data=EXAMPLE_LOS_DATA[3],
            )
            self.create_speakers_for_los(
                los_id=550,
                base_speaker_id=23,
                speaker_data=EXAMPLE_LOS_DATA[4],
            )
            self.create_poocs(
                {
                    1: {
                        1: ("Big point", 1, [8, 20, 21]),
                        2: ("A point", 2, [9]),
                        3: ("Small point", 3, [22]),
                    },
                    4: {
                        4: ("You have", 1, []),
                        5: ("A point", 2, []),
                        6: ("A", 3, []),
                        7: ("Small point", 4, []),
                    },
                }
            )
            self.create_sllos(
                {
                    330: EXAMPLE_SLLOS_DATA[0],
                    440: EXAMPLE_SLLOS_DATA[1],
                    550: EXAMPLE_SLLOS_DATA[2],
                }
            )
        if with_mediafiles:
            orga_data = {
                "owner_id": ONE_ORGANIZATION_FQID,
                "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
            }

            self.set_models(
                {
                    ONE_ORGANIZATION_FQID: {
                        "mediafile_ids": [1, 2, 3, 4, 5],
                        "published_mediafile_ids": [1, 2, 3, 4, 5],
                    },
                    "meeting/1": {
                        "mediafile_ids": [6, 7, 8, 9, 10],
                        "meeting_mediafile_ids": [21, 31, 41],
                    },
                    "meeting/4": {
                        "meeting_mediafile_ids": [24, 34, 44, 54],
                    },
                    "mediafile/1": {
                        "child_ids": [2, 3],
                        "is_directory": True,
                        "create_timestamp": 100,
                        **self.get_mediafile_data("A"),
                        **orga_data,
                    },
                    "mediafile/2": {
                        "parent_id": 1,
                        "child_ids": [4],
                        "is_directory": True,
                        "filesize": 100,
                        "create_timestamp": 200,
                        **self.get_mediafile_data("B"),
                        **orga_data,
                        "meeting_mediafile_ids": [21, 24],
                    },
                    "meeting_mediafile/21": {
                        "mediafile_id": 2,
                        "meeting_id": 1,
                    },
                    "meeting_mediafile/24": {
                        "mediafile_id": 2,
                        "meeting_id": 4,
                    },
                    "mediafile/3": {
                        "parent_id": 1,
                        "create_timestamp": 300,
                        **self.get_mediafile_data("C", "txt"),
                        **orga_data,
                        "meeting_mediafile_ids": [31, 34],
                    },
                    "meeting_mediafile/31": {
                        "mediafile_id": 3,
                        "meeting_id": 1,
                    },
                    "meeting_mediafile/34": {
                        "mediafile_id": 3,
                        "meeting_id": 4,
                    },
                    "mediafile/4": {
                        "parent_id": 2,
                        "filesize": 200,
                        "create_timestamp": 400,
                        **self.get_mediafile_data("D", "png"),
                        **orga_data,
                        "meeting_mediafile_ids": [41, 44],
                    },
                    "meeting_mediafile/41": {
                        "mediafile_id": 4,
                        "meeting_id": 1,
                    },
                    "meeting_mediafile/44": {
                        "mediafile_id": 4,
                        "meeting_id": 4,
                    },
                    "mediafile/5": {
                        "filesize": 300,
                        "create_timestamp": 500,
                        **self.get_mediafile_data("E", "png"),
                        **orga_data,
                        "meeting_mediafile_ids": [51],
                    },
                    "meeting_mediafile/51": {
                        "mediafile_id": 5,
                        "meeting_id": 1,
                    },
                    # Meeting specific
                    "mediafile/6": {
                        "owner_id": "meeting/1",
                        "filesize": 150,
                        "create_timestamp": 600,
                        **self.get_mediafile_data("F", "pdf"),
                        "meeting_mediafile_ids": [61],
                    },
                    "meeting_mediafile/61": {
                        "mediafile_id": 6,
                        "meeting_id": 1,
                    },
                    "mediafile/7": {
                        "owner_id": "meeting/1",
                        "child_ids": [8],
                        "is_directory": True,
                        "create_timestamp": 700,
                        **self.get_mediafile_data("G"),
                        "meeting_mediafile_ids": [71],
                    },
                    "meeting_mediafile/71": {
                        "mediafile_id": 7,
                        "meeting_id": 1,
                    },
                    "mediafile/8": {
                        "owner_id": "meeting/1",
                        "parent_id": 7,
                        "child_ids": [9],
                        "is_directory": True,
                        "create_timestamp": 800,
                        **self.get_mediafile_data("H"),
                        "meeting_mediafile_ids": [81],
                    },
                    "meeting_mediafile/81": {
                        "mediafile_id": 8,
                        "meeting_id": 1,
                    },
                    "mediafile/9": {
                        "owner_id": "meeting/1",
                        "parent_id": 8,
                        "child_ids": [10],
                        "is_directory": True,
                        "create_timestamp": 900,
                        **self.get_mediafile_data("I"),
                        "meeting_mediafile_ids": [91],
                    },
                    "meeting_mediafile/91": {
                        "mediafile_id": 9,
                        "meeting_id": 1,
                    },
                    "mediafile/10": {
                        "owner_id": "meeting/1",
                        "parent_id": 9,
                        "filesize": 100,
                        "create_timestamp": 1000,
                        **self.get_mediafile_data("J", "txt"),
                        "meeting_mediafile_ids": [101],
                    },
                    "meeting_mediafile/101": {
                        "mediafile_id": 10,
                        "meeting_id": 1,
                    },
                }
            )
            self.add_meeting_mediafiles_to_topics(
                {
                    44: [31, 51, 101],  # Some leafs
                    55: [31, 41, 51, 61, 101],  # All leafs
                    66: [21, 31, 51, 61, 71],  # All root-level
                }
            )

    def assert_full_dataset(
        self,
        forwarded_ids: list[int],
        to_ids: list[int],
        with_speakers: bool = False,
        with_moderator_notes: bool = False,
        next_agenda_id: int = 8,
        next_topic_id: int = 78,
        next_los_id: int = 771,
        base_agenda_weight_per_meeting: dict[int, int] = {4: 0, 7: 7},
    ) -> tuple[
        dict[int, dict[int, int]], dict[int, dict[int, int]], dict[int, dict[int, int]]
    ]:
        """
        Tests if the content of agenda_items, topics and attachments is correct.
        Returns the old_id to new_id matches per meeting for agenda_item, topic and los
        """
        # agenda_item_id = agenda_item data, topic data, los data
        expected_agenda_creation_order: list[
            tuple[int, tuple[dict[str, Any], dict[str, Any]]]
        ] = [
            (
                1,
                (
                    {},
                    {
                        "closed": True,
                        "moderator_notes": "This is a short mod note.",
                    },
                ),
            ),
            (
                6,
                (
                    {
                        "comment": "This one is hidden.",
                        "type": "hidden",
                    },
                    {"closed": True},
                ),
            ),
            (
                2,
                (
                    {
                        "comment": "This is a comment.",
                        "type": "internal",
                    },
                    {"moderator_notes": "This is a slightly longer mod note."},
                ),
            ),
            (3, ({}, {})),
            (4, ({}, {})),
            (5, ({}, {})),
        ]
        id_to_in_order_parents = {1: [], 2: [1], 3: [1], 4: [2, 1], 5: [2, 1], 6: []}
        model_matches: tuple[
            dict[int, dict[int, int]],
            dict[int, dict[int, int]],
            dict[int, dict[int, int]],
        ] = (
            {},
            {},
            {},
        )
        for meeting_id in to_ids:
            for i in range(3):
                model_matches[i][meeting_id] = {}
            for id_, data in expected_agenda_creation_order:
                if id_ in forwarded_ids:
                    parent_id = next(
                        (i for i in id_to_in_order_parents[id_] if i in forwarded_ids),
                        None,
                    )
                    model_matches[0][meeting_id][id_] = next_agenda_id
                    model_matches[1][meeting_id][id_ * 11] = next_topic_id
                    model_matches[2][meeting_id][id_ * 110] = next_los_id

                    self.assert_model_exists(
                        f"agenda_item/{next_agenda_id}",
                        {
                            "content_object_id": f"topic/{next_topic_id}",
                            "meeting_id": meeting_id,
                            "tag_ids": None,
                            "weight": id_ + base_agenda_weight_per_meeting[meeting_id],
                            **(
                                {"parent_id": model_matches[0][meeting_id][parent_id]}
                                if parent_id
                                else {}
                            ),
                            **{field: val for field, val in data[0].items()},
                        },
                    )
                    self.assert_model_exists(
                        f"topic/{next_topic_id}",
                        {
                            "agenda_item_id": next_agenda_id,
                            "list_of_speakers_id": next_los_id,
                            "meeting_id": meeting_id,
                            "title": f"Topic {id_*11}",
                            "text": f"This is the text of topic {id_*11}",
                        },
                    )
                    self.assert_model_exists(
                        f"list_of_speakers/{next_los_id}",
                        {
                            "content_object_id": f"topic/{next_topic_id}",
                            "meeting_id": meeting_id,
                            **{
                                field: val
                                for field, val in data[1].items()
                                if (field != "closed" or with_speakers)
                                and (field != "moderator_notes" or with_moderator_notes)
                            },
                        },
                    )

                    next_agenda_id += 1
                    next_topic_id += 1
                    next_los_id += 1
        self.assert_model_not_exists(f"agenda_item/{next_agenda_id}")
        self.assert_model_not_exists(f"topic/{next_topic_id}")
        self.assert_model_not_exists(f"list_of_speakers/{next_los_id}")
        return model_matches

    def assert_group_data(self, expected_group_data: dict[int, dict[int, str]]) -> None:
        """
        Takes group data in the format
        {
            meeting_id: { group_id: name }
        }
        and checks if this represents the current state of the data.
        """
        for meeting_id, meeting_group_data in expected_group_data.items():
            for group_id, name in meeting_group_data.items():
                self.assert_model_exists(
                    f"group/{group_id}", {"meeting_id": meeting_id, "name": name}
                )

    def assert_structure_level_data(
        self,
        expected_structure_level_data: dict[int, dict[int, tuple[str, str | None]]],
    ) -> None:
        """
        Takes structure_level data in the format
        {
            meeting_id: { structure_level_id: ( name, color ) }
        }
        and checks if this represents the current state of the data.
        """
        for (
            meeting_id,
            meeting_structure_level_data,
        ) in expected_structure_level_data.items():
            for structure_level_id, data in meeting_structure_level_data.items():
                self.assert_model_exists(
                    f"structure_level/{structure_level_id}",
                    {"meeting_id": meeting_id, "name": data[0], "color": data[1]},
                )

    def assert_meeting_user_data(
        self,
        expected_meeting_user_data: dict[
            int,
            dict[int, tuple[int, list[int], list[int] | None, dict[str, str | None]]],
        ],
    ) -> None:
        """
        Takes meeting_user data in the format
        {
            meeting_id: { meeting_user_id: (
                user_id,
                group_ids,
                structure_level_ids,
                transferable_meeting_user_data
            ) }
        }
        and checks if this represents the current state of the data.
        """
        for meeting_id, meeting_muser_data in expected_meeting_user_data.items():
            for muser_id, data in meeting_muser_data.items():
                self.assert_model_exists(
                    f"meeting_user/{muser_id}",
                    {
                        "meeting_id": meeting_id,
                        "user_id": data[0],
                        "group_ids": data[1],
                        "structure_level_ids": data[2],
                        **data[3],
                    },
                )

    def assert_speaker_data(
        self,
        expected_speaker_data: dict[int, dict[int, list[tuple[int, SpeakerData]]]],
        meeting_id_to_old_to_new_muser_id: dict[int, dict[int, int]],
    ) -> None:
        """
        Takes speaker data in the format
        {
            meeting_id: { los_id: [ ( speaker_id, SpeakerData ) ] }
        }
        and checks if this represents the current state of the data.
        """
        for meeting_id, meeting_speaker_data in expected_speaker_data.items():
            for los_id, los_speaker_data in meeting_speaker_data.items():
                for speaker_id, date in los_speaker_data:
                    self.assert_model_exists(
                        f"speaker/{speaker_id}",
                        {
                            "meeting_id": meeting_id,
                            "list_of_speakers_id": los_id,
                            "meeting_user_id": meeting_id_to_old_to_new_muser_id[
                                meeting_id
                            ][date[7]],
                            **{
                                field: val
                                for j, field in enumerate(
                                    [
                                        "begin_time",
                                        "end_time",
                                        "total_pause",
                                        "speech_state",
                                        "answer",
                                        "note",
                                        "point_of_order",
                                    ]
                                )
                                if (val := date[j]) is not None
                            },
                        },
                    )

    def assert_sllos_data(
        self,
        expected_sllos_data: dict[int, dict[int, list[tuple[int, SLLOSData]]]],
        meeting_to_old_to_new_structure_level_id: dict[int, dict[int, int]],
        meeting_to_old_to_new_speaker_id: dict[int, dict[int, int]],
    ) -> None:
        """
        Takes sllos data in the format
        {
            meeting_id: { los_id: [ ( sllos_id, SLLOSData ) ] }
        }
        and checks if this represents the current state of the data.
        """
        for meeting_id, meeting_sllos_data in expected_sllos_data.items():
            for los_id, los_sllos_data in meeting_sllos_data.items():
                for sllos_id, sllos_date in los_sllos_data:
                    (
                        structure_level_id,
                        initial_time,
                        additional_time,
                        remaining_time,
                        speaker_ids,
                    ) = sllos_date
                    self.assert_model_exists(
                        f"structure_level_list_of_speakers/{sllos_id}",
                        {
                            "meeting_id": meeting_id,
                            "list_of_speakers_id": los_id,
                            "structure_level_id": meeting_to_old_to_new_structure_level_id[
                                meeting_id
                            ][
                                structure_level_id
                            ],
                            "initial_time": initial_time,
                            "remaining_time": remaining_time,
                            "speaker_ids": [
                                meeting_to_old_to_new_speaker_id[meeting_id][s_id]
                                for s_id in speaker_ids
                            ],
                            **(
                                {"additional_time": additional_time}
                                if additional_time is not None
                                else {}
                            ),
                        },
                    )

    def assert_pooc_data(
        self, expected_pooc_data: dict[int, dict[int, tuple[str, int, list[int]]]]
    ) -> None:
        """
        Takes pooc data in the format
        {
            meeting_id: {
                pooc_id: ( text, rank, new_speaker_ids )
            }
        }
        and checks if this represents the current state of the data.
        """
        for meeting_id, meeting_pooc_data in expected_pooc_data.items():
            for pooc_id, data in meeting_pooc_data.items():
                self.assert_model_exists(
                    f"point_of_order_category/{pooc_id}",
                    {
                        "meeting_id": meeting_id,
                        "text": data[0],
                        "rank": data[1],
                        "speaker_ids": data[2],
                    },
                )

    def assert_mediafile_data(
        self,
        expected_mediafile_data: dict[
            str,
            dict[
                int,
                tuple[
                    dict[str, Any],
                    tuple[str, FileEndString | None],
                    dict[int, tuple[int, list[int], dict[str, Any]]],
                ],
            ],
        ],
    ) -> None:
        """
        Takes mediafile data in the format
        {
            owner_id: {
                mediafile_id: (
                    { mediafile_key: value },
                    ( file_name, file_ending ),
                    {
                        meeting_mediafile_id: (
                            meeting_id,
                            attachment_topic_ids,
                            meeting_mediafile_data
                        )
                    }
                )
            }
        }
        and checks if this represents the current state of the data.
        The method assumes that all orga files are published.
        """
        for owner_id, owner_data in expected_mediafile_data.items():
            data: dict[str, Any] = {"owner_id": owner_id}
            if owner_id == ONE_ORGANIZATION_FQID:
                data.update(
                    {
                        "owner_id": ONE_ORGANIZATION_FQID,
                        "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                    }
                )
            for mediafile_id, mediafile_data in owner_data.items():
                self.assert_model_exists(
                    f"mediafile/{mediafile_id}",
                    {
                        **data,
                        **mediafile_data[0],
                        **self.get_mediafile_data(*mediafile_data[1]),
                        "meeting_mediafile_ids": (
                            list(mediafile_data[2].keys())
                            if mediafile_data[2]
                            else None
                        ),
                    },
                )
                for mmediafile_id, mmediafile_data in mediafile_data[2].items():
                    self.assert_model_exists(
                        f"meeting_mediafile/{mmediafile_id}",
                        {
                            "meeting_id": mmediafile_data[0],
                            "mediafile_id": mediafile_id,
                            "attachment_ids": (
                                [
                                    f"topic/{topic_id}"
                                    for topic_id in sorted(mmediafile_data[1])
                                ]
                                if mmediafile_data[1]
                                else None
                            ),
                            **mmediafile_data[2],
                        },
                    )

    def test_simple(self) -> None:
        self.create_meeting()
        self.create_meeting(4)
        self.create_meeting(7)
        self.set_models(
            {
                "committee/60": {"forward_agenda_to_committee_ids": [63, 66]},
                "committee/63": {"receive_agenda_forwardings_from_committee_ids": [60]},
                "committee/67": {"receive_agenda_forwardings_from_committee_ids": [60]},
            }
        )
        self.create_topic_agenda_item(
            extra_los_fields={
                "closed": True,
                "moderator_notes": "This LoS was closed because we hate this topic. This is definitely personal.",
            }
        )  # 1
        self.create_topic_agenda_item(2, 20, parent_id=1)  # 3
        self.create_topic_agenda_item(3, 30, parent_id=1)  # 4
        self.create_topic_agenda_item(4, 40, parent_id=2)  # 5
        self.create_topic_agenda_item(5, 50)
        self.create_topic_agenda_item(
            6,
            60,
            parent_id=5,
            extra_agenda_fields={
                "item_number": "TOP 6",
                "comment": "This topic has no parent, so it will be copied before any topic without parents.",
                "closed": True,
                "type": "internal",
                "duration": 600,
                "is_internal": True,
            },
        )  # 2
        self.create_topic_agenda_item(
            7, 70, parent_id=6, extra_agenda_fields={"is_internal": True}
        )
        self.create_topic_agenda_item(
            8, 80, parent_id=7, extra_agenda_fields={"is_internal": True}
        )
        self.create_topic_agenda_item(
            9, 90, parent_id=8, extra_agenda_fields={"is_internal": True}
        )  # 6

        response = self.request(
            "agenda_item.forward",
            {
                "meeting_ids": [4, 7],
                "agenda_item_ids": [1, 2, 3, 4, 6, 9],
            },
        )
        self.assert_status_code(response, 200)

        def assert_agenda_item_copy(
            meeting_id: int,
            meeting_copy_order: int,
            original_order: int,
            parent_meeting_copy_order: int | None = None,
            children_meeting_copy_orders: list[int] | None = None,
            previous_meeting_copies_amount: int = 0,
            extra_agenda_fields: dict[str, Any] = {},
        ) -> None:
            copy_order = previous_meeting_copies_amount + meeting_copy_order
            self.assert_model_exists(
                f"topic/{90 + copy_order}",
                {
                    "agenda_item_id": 9 + copy_order,
                    "list_of_speakers_id": 900 + copy_order,
                    "meeting_id": meeting_id,
                    "title": f"Topic {original_order * 10}",
                    "text": f"This is the text of topic {original_order * 10}",
                    "sequential_number": meeting_copy_order,
                },
            )
            agenda_item = self.assert_model_exists(
                f"agenda_item/{9 + copy_order}",
                {
                    "content_object_id": f"topic/{90 + copy_order}",
                    "meeting_id": meeting_id,
                    "weight": original_order,
                    "is_internal": False,
                    **extra_agenda_fields,
                },
            )
            if parent_meeting_copy_order:
                assert (
                    agenda_item["parent_id"]
                    == 9 + previous_meeting_copies_amount + parent_meeting_copy_order
                )
            else:
                assert not agenda_item.get("parent_id")
            if children_meeting_copy_orders:
                assert agenda_item["child_ids"] == [
                    9 + previous_meeting_copies_amount + val
                    for val in children_meeting_copy_orders
                ]
            else:
                assert not agenda_item.get("child_ids")
            self.assert_model_exists(
                f"list_of_speakers/{900 + copy_order}",
                {
                    "content_object_id": f"topic/{90 + copy_order}",
                    "meeting_id": meeting_id,
                    "sequential_number": meeting_copy_order,
                    "speaker_ids": None,
                    "structure_level_list_of_speakers_ids": None,
                    "closed": False,
                    "moderator_notes": None,
                },
            )

        assert_agenda_item_copy(
            meeting_id=4,
            meeting_copy_order=1,
            original_order=1,
            children_meeting_copy_orders=[3, 4],
        )
        assert_agenda_item_copy(
            meeting_id=4,
            meeting_copy_order=2,
            original_order=6,
            children_meeting_copy_orders=[6],
            extra_agenda_fields={
                "item_number": None,  # Not transferred
                "comment": "This topic has no parent, so it will be copied before any topic without parents.",
                "closed": False,  # Not transferred -> default
                "type": "internal",
                "duration": None,  # Not transferred
                "is_internal": True,  # Calculated
            },
        )
        assert_agenda_item_copy(
            meeting_id=4,
            meeting_copy_order=3,
            original_order=2,
            parent_meeting_copy_order=1,
            children_meeting_copy_orders=[5],
        )
        assert_agenda_item_copy(
            meeting_id=4,
            meeting_copy_order=4,
            original_order=3,
            parent_meeting_copy_order=1,
        )
        assert_agenda_item_copy(
            meeting_id=4,
            meeting_copy_order=5,
            original_order=4,
            parent_meeting_copy_order=3,
        )
        assert_agenda_item_copy(
            meeting_id=4,
            meeting_copy_order=6,
            original_order=9,
            parent_meeting_copy_order=2,
            extra_agenda_fields={"is_internal": True},  # Calculated
        )

        assert_agenda_item_copy(
            meeting_id=7,
            meeting_copy_order=1,
            original_order=1,
            children_meeting_copy_orders=[3, 4],
            previous_meeting_copies_amount=6,
        )
        assert_agenda_item_copy(
            meeting_id=7,
            meeting_copy_order=2,
            original_order=6,
            children_meeting_copy_orders=[6],
            previous_meeting_copies_amount=6,
            extra_agenda_fields={
                "item_number": None,  # Not transferred
                "comment": "This topic has no parent, so it will be copied before any topic without parents.",
                "closed": False,  # Not transferred -> default
                "type": "internal",
                "duration": None,  # Not transferred
                "is_internal": True,  # Calculated
            },
        )
        assert_agenda_item_copy(
            meeting_id=7,
            meeting_copy_order=3,
            original_order=2,
            parent_meeting_copy_order=1,
            children_meeting_copy_orders=[5],
            previous_meeting_copies_amount=6,
        )
        assert_agenda_item_copy(
            meeting_id=7,
            meeting_copy_order=4,
            original_order=3,
            parent_meeting_copy_order=1,
            previous_meeting_copies_amount=6,
        )
        assert_agenda_item_copy(
            meeting_id=7,
            meeting_copy_order=5,
            original_order=4,
            parent_meeting_copy_order=3,
            previous_meeting_copies_amount=6,
        )
        assert_agenda_item_copy(
            meeting_id=7,
            meeting_copy_order=6,
            original_order=9,
            parent_meeting_copy_order=2,
            previous_meeting_copies_amount=6,
            extra_agenda_fields={"is_internal": True},  # Calculated
        )
        for collection in [
            "mediafile",
            "meeting_mediafile",
            "speaker",
            "structure_level_list_of_speakers",
            "point_of_order_category",
            "structure_level",
            "meeting_user",
        ]:
            self.assert_model_not_exists(f"{collection}/1")
        self.assert_model_not_exists("group/10")

    def test_simple_with_all_flags(self) -> None:
        self.create_meeting()
        self.create_meeting(4)
        self.set_models(
            {
                "committee/60": {"forward_agenda_to_committee_ids": [63]},
                "committee/63": {"receive_agenda_forwardings_from_committee_ids": [60]},
            }
        )
        self.create_topic_agenda_item(
            extra_los_fields={
                "closed": True,
                "moderator_notes": "This LoS was closed because we hate this topic. This is definitely personal.",
            }
        )  # 1
        self.create_topic_agenda_item(2, 20, parent_id=1)  # 3
        self.create_topic_agenda_item(3, 30, parent_id=1)  # 4
        self.create_topic_agenda_item(4, 40, parent_id=3)  # 5
        self.create_topic_agenda_item(5, 50)
        self.create_topic_agenda_item(6, 60, parent_id=5)
        self.create_topic_agenda_item(7, 70, parent_id=6)  # 2
        self.create_topic_agenda_item(8, 80, parent_id=7)
        self.create_topic_agenda_item(9, 90, parent_id=8)  # 6

        response = self.request(
            "agenda_item.forward",
            {
                "meeting_ids": [4],
                "agenda_item_ids": [1, 2, 3, 4, 6, 9],
                "with_speakers": True,
                "with_moderator_notes": True,
                "with_attachments": True,
            },
        )
        self.assert_status_code(response, 200)

        def assert_agenda_item_copy(
            meeting_id: int,
            meeting_copy_order: int,
            original_order: int,
            parent_meeting_copy_order: int | None = None,
            children_meeting_copy_orders: list[int] | None = None,
            previous_meeting_copies_amount: int = 0,
            extra_los_fields: dict[str, Any] = {},
        ) -> None:
            copy_order = previous_meeting_copies_amount + meeting_copy_order
            self.assert_model_exists(
                f"topic/{90 + copy_order}",
                {
                    "agenda_item_id": 9 + copy_order,
                    "list_of_speakers_id": 900 + copy_order,
                    "meeting_id": meeting_id,
                    "title": f"Topic {original_order * 10}",
                    "text": f"This is the text of topic {original_order * 10}",
                    "sequential_number": meeting_copy_order,
                },
            )
            agenda_item = self.assert_model_exists(
                f"agenda_item/{9 + copy_order}",
                {
                    "content_object_id": f"topic/{90 + copy_order}",
                    "meeting_id": meeting_id,
                    "weight": original_order,
                },
            )
            if parent_meeting_copy_order:
                assert (
                    agenda_item["parent_id"]
                    == 9 + previous_meeting_copies_amount + parent_meeting_copy_order
                )
            else:
                assert not agenda_item.get("parent_id")
            if children_meeting_copy_orders:
                assert agenda_item["child_ids"] == [
                    9 + previous_meeting_copies_amount + val
                    for val in children_meeting_copy_orders
                ]
            else:
                assert not agenda_item.get("child_ids")
            self.assert_model_exists(
                f"list_of_speakers/{900 + copy_order}",
                {
                    "content_object_id": f"topic/{90 + copy_order}",
                    "meeting_id": meeting_id,
                    "sequential_number": meeting_copy_order,
                    "speaker_ids": None,
                    "structure_level_list_of_speakers_ids": None,
                    "closed": False,
                    "moderator_notes": None,
                    **extra_los_fields,
                },
            )

        assert_agenda_item_copy(
            meeting_id=4,
            meeting_copy_order=1,
            original_order=1,
            children_meeting_copy_orders=[3, 4],
            extra_los_fields={
                "closed": True,
                "moderator_notes": "This LoS was closed because we hate this topic. This is definitely personal.",
            },
        )
        assert_agenda_item_copy(
            meeting_id=4,
            meeting_copy_order=2,
            original_order=6,
            children_meeting_copy_orders=[6],
        )
        assert_agenda_item_copy(
            meeting_id=4,
            meeting_copy_order=3,
            original_order=2,
            parent_meeting_copy_order=1,
        )
        assert_agenda_item_copy(
            meeting_id=4,
            meeting_copy_order=4,
            original_order=3,
            parent_meeting_copy_order=1,
            children_meeting_copy_orders=[5],
        )
        assert_agenda_item_copy(
            meeting_id=4,
            meeting_copy_order=5,
            original_order=4,
            parent_meeting_copy_order=4,
        )
        assert_agenda_item_copy(
            meeting_id=4,
            meeting_copy_order=6,
            original_order=9,
            parent_meeting_copy_order=2,
        )
        for collection in [
            "mediafile",
            "meeting_mediafile",
            "speaker",
            "structure_level_list_of_speakers",
            "point_of_order_category",
            "structure_level",
            "meeting_user",
        ]:
            self.assert_model_not_exists(f"{collection}/1")
        self.assert_model_not_exists("group/7")

    def test_full_dataset_everything_everywhere_no_flags(self) -> None:
        self.create_full_dataset()

        response = self.request(
            "agenda_item.forward",
            {
                "meeting_ids": [4, 7],
                "agenda_item_ids": [1, 2, 3, 4, 5, 6],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_full_dataset([1, 2, 3, 4, 5, 6], [4, 7])
        for collection, id_ in {
            "mediafile": 11,
            "meeting_mediafile": 102,
            "speaker": 29,
            "structure_level_list_of_speakers": 15,
            "point_of_order_category": 8,
            "structure_level": 21,
            "meeting_user": 18,
        }.items():
            self.assert_model_not_exists(f"{collection}/{id_}")
        self.assert_model_not_exists("group/10")

    def test_full_dataset_everything_everywhere_all_flags(self) -> None:
        self.create_full_dataset()
        self.set_models(
            {
                "meeting/4": {"list_of_speakers_default_structure_level_time": 60},
                "meeting/7": {"list_of_speakers_default_structure_level_time": 60},
            }
        )

        response = self.request(
            "agenda_item.forward",
            {
                "meeting_ids": [4, 7],
                "agenda_item_ids": [1, 2, 3, 4, 5, 6],
                "with_speakers": True,
                "with_moderator_notes": True,
                "with_attachments": True,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_full_dataset(
            [1, 2, 3, 4, 5, 6], [4, 7], with_speakers=True, with_moderator_notes=True
        )
        self.assert_group_data(
            {
                4: {10: "Delegate"},
                7: {
                    11: "Default",
                    12: "Admin",
                    13: "Delegate",
                },
            }
        )
        meeting_to_old_to_new_structure_level_id: dict[int, dict[int, int]] = {
            4: {
                1: 13,
                2: 14,
                3: 21,
                4: 15,
                5: 22,
                6: 23,
                7: 24,
                8: 25,
                9: 26,
                10: 27,
                11: 28,
                12: 29,
            },
            7: {id_: id_ + 29 for id_ in range(1, 13)},
        }
        self.assert_structure_level_data(
            {
                4: {
                    13: ("red", None),
                    14: ("orange", "#ff8000"),
                    15: ("green", "#00ff33"),
                    16: ("ocean", "#0000ff"),
                    17: ("whitecat", "#ffffff"),
                    18: ("greycat", "#808080"),
                    19: ("blackcat", "#000000"),
                    20: ("void", None),
                    21: ("yellow", "#ffff00"),
                    22: ("cyan", "#00ffff"),
                    23: ("blue", "#0000ff"),
                    24: ("pink", "#ff00ff"),
                    25: ("purple", "#8000ff"),
                    26: ("white", "#ffffff"),
                    27: ("grey", "#808080"),
                    28: ("black", "#000000"),
                    29: ("nothing", None),
                },
                7: {
                    30: ("red", "#ff0000"),
                    31: ("orange", "#ff8000"),
                    32: ("yellow", "#ffff00"),
                    33: ("green", "#00ff00"),
                    34: ("cyan", "#00ffff"),
                    35: ("blue", "#0000ff"),
                    36: ("pink", "#ff00ff"),
                    37: ("purple", "#8000ff"),
                    38: ("white", "#ffffff"),
                    39: ("grey", "#808080"),
                    40: ("black", "#000000"),
                    41: ("nothing", None),
                },
            }
        )

        def get_meeting_user_data(id_: int) -> dict[str, str | None]:
            return {
                field: (val if len(field) - 6 != id_ % 3 else None)
                for field, val in [
                    ("number", f"MTNGUSR{id_}"),
                    ("comment", f"Comment of meeting user{id_}"),
                    ("about_me", f"I am meeting user {id_}"),
                ]
            }

        meeting_id_to_old_to_new_muser_id: dict[int, dict[int, int]] = {
            4: {
                1: 2,
                4: 18,
                5: 19,
                6: 20,
                7: 21,
                8: 22,
                9: 10,
                11: 12,
                13: 14,
                16: 17,
            },
            7: {
                1: 3,
                4: 23,
                5: 24,
                6: 25,
                7: 26,
                8: 27,
                9: 28,
                11: 29,
                13: 15,
                16: 30,
            },
        }
        self.assert_meeting_user_data(
            {
                4: {
                    2: (1, [4, 5], [17], get_meeting_user_data(2)),  # Take 4 add 5
                    18: (2, [4], [13], get_meeting_user_data(4)),  # From meeting_user 4
                    19: (3, [5], [14], get_meeting_user_data(5)),  # From meeting_user 5
                    20: (
                        4,
                        [10],
                        [21],
                        get_meeting_user_data(6),
                    ),  # From meeting_user 6
                    21: (
                        5,
                        [4, 5],
                        [29],
                        get_meeting_user_data(7),
                    ),  # From meeting_user 7
                    22: (
                        6,
                        [5, 10],
                        [14, 15, 23, 25, 27, 29],
                        get_meeting_user_data(8),
                    ),  # From meeting_user 8
                    10: (
                        7,
                        [4, 10],
                        [13, 14, 15],
                        get_meeting_user_data(10),
                    ),  # Take 4 add 10
                    12: (
                        8,
                        [5],
                        [16, 17, 18, 19, 20],
                        get_meeting_user_data(12),
                    ),  # Take 5
                    14: (9, [6, 10], [], get_meeting_user_data(14)),  # Take 6 add 10
                    17: (
                        10,
                        [4, 5],
                        [14, 16, 18, 20],
                        get_meeting_user_data(17),
                    ),  # Take 4 add 5
                },
                7: {
                    3: (
                        1,
                        [8, 9, 12],
                        None,
                        get_meeting_user_data(3),
                    ),  # Take 8, 9 add 12
                    23: (
                        2,
                        [11],
                        [30],
                        get_meeting_user_data(4),
                    ),  # From meeting_user 4
                    24: (
                        3,
                        [12],
                        [31],
                        get_meeting_user_data(5),
                    ),  # From meeting_user 5
                    25: (
                        4,
                        [13],
                        [32],
                        get_meeting_user_data(6),
                    ),  # From meeting_user 6
                    26: (
                        5,
                        [11, 12],
                        [41],
                        get_meeting_user_data(7),
                    ),  # From meeting_user 7
                    27: (
                        6,
                        [12, 13],
                        [31, 33, 35, 37, 39, 41],
                        get_meeting_user_data(8),
                    ),  # From meeting_user 8
                    28: (
                        7,
                        [13],
                        [30, 32, 34, 36, 38, 40],
                        get_meeting_user_data(9),
                    ),  # From meeting_user 9
                    29: (
                        8,
                        [12],
                        [],
                        get_meeting_user_data(11),
                    ),  # From meeting_user 11
                    15: (9, [9, 13], None, get_meeting_user_data(15)),  # Take 9 add 13
                    30: (
                        10,
                        [11, 12],
                        list(range(30, 42)),
                        get_meeting_user_data(16),
                    ),  # From meeting_user 16
                },
            }
        )
        meeting_to_old_to_new_speaker_id = {
            4: {old_id: old_id + 28 for old_id in range(1, 29)},
            7: {old_id: old_id + 56 for old_id in range(1, 29)},
        }
        # {meeting_id -> {los_id -> (speaker_id, SpeakerData)[]}}
        self.assert_speaker_data(
            {
                4: {
                    771: list(
                        enumerate(EXAMPLE_LOS_DATA[0], 29)
                    ),  # 110, speaker 1-4 -> 29-32
                    773: list(
                        enumerate(EXAMPLE_LOS_DATA[1], 33)
                    ),  # 220, speaker 5-9 -> 33-37
                    774: list(
                        enumerate(EXAMPLE_LOS_DATA[2], 38)
                    ),  # 330, speaker 10-19 -> 38-47
                    775: list(
                        enumerate(EXAMPLE_LOS_DATA[3], 48)
                    ),  # 440, speaker 20-22 -> 48-50
                    776: list(
                        enumerate(EXAMPLE_LOS_DATA[4], 51)
                    ),  # 550, speaker 23-28 -> 51-56
                },
                7: {
                    777: list(
                        enumerate(EXAMPLE_LOS_DATA[0], 57)
                    ),  # 110, speaker 1-4 -> 57-60
                    779: list(
                        enumerate(EXAMPLE_LOS_DATA[1], 61)
                    ),  # 220, speaker 5-9 -> 61-65
                    780: list(
                        enumerate(EXAMPLE_LOS_DATA[2], 66)
                    ),  # 330, speaker 10-19 -> 66-75
                    781: list(
                        enumerate(EXAMPLE_LOS_DATA[3], 76)
                    ),  # 440, speaker 20-22 -> 76-78
                    782: list(
                        enumerate(EXAMPLE_LOS_DATA[4], 79)
                    ),  # 550, speaker 23-28 -> 79-84
                },
            },
            meeting_id_to_old_to_new_muser_id,
        )
        next_sllos_id = sum(len(sllos) for sllos in EXAMPLE_SLLOS_DATA) + 1
        self.assert_sllos_data(
            {
                4: {
                    774: list(enumerate(EXAMPLE_SLLOS_DATA[0], next_sllos_id)),
                    775: list(enumerate(EXAMPLE_SLLOS_DATA[1], next_sllos_id + 7)),
                    776: list(enumerate(EXAMPLE_SLLOS_DATA[2], next_sllos_id + 9)),
                },
                7: {
                    780: list(enumerate(EXAMPLE_SLLOS_DATA[0], next_sllos_id + 14)),
                    781: list(enumerate(EXAMPLE_SLLOS_DATA[1], next_sllos_id + 21)),
                    782: list(enumerate(EXAMPLE_SLLOS_DATA[2], next_sllos_id + 23)),
                },
            },
            meeting_to_old_to_new_structure_level_id,
            meeting_to_old_to_new_speaker_id,
        )
        self.assert_pooc_data(
            {
                4: {
                    4: ("You have", 1, []),
                    5: ("A point", 2, [37]),
                    6: ("A", 3, []),
                    7: ("Small point", 4, [50]),
                    8: ("Big point", 1, [36, 48, 49]),  # new
                },
                7: {
                    9: ("Big point", 1, [64, 76, 77]),  # new
                    10: ("A point", 2, [65]),  # new
                    11: ("Small point", 3, [78]),  # new
                },
            }
        )
        self.assert_mediafile_data(
            {
                ONE_ORGANIZATION_FQID: {
                    1: (
                        {
                            "child_ids": [2, 3],
                            "is_directory": True,
                            "create_timestamp": 100,
                        },
                        ("A", None),
                        {},
                    ),
                    2: (
                        {
                            "parent_id": 1,
                            "child_ids": [4],
                            "is_directory": True,
                            "filesize": 100,
                            "create_timestamp": 200,
                        },
                        ("B", None),
                        {
                            21: (1, [66], {}),
                            24: (4, [79], {}),
                            113: (
                                7,
                                [85],
                                {
                                    "is_public": False,
                                    "access_group_ids": None,
                                    "inherited_access_group_ids": [8],
                                },
                            ),
                        },
                    ),
                    3: (
                        {
                            "parent_id": 1,
                            "create_timestamp": 300,
                        },
                        ("C", "txt"),
                        {
                            31: (1, [44, 55, 66], {}),
                            34: (4, [82, 83, 79], {}),
                            114: (
                                7,
                                [88, 89, 85],
                                {
                                    "is_public": False,
                                    "access_group_ids": None,
                                    "inherited_access_group_ids": [8],
                                },
                            ),
                        },
                    ),
                    4: (
                        {
                            "parent_id": 2,
                            "filesize": 200,
                            "create_timestamp": 400,
                        },
                        ("D", "png"),
                        {
                            41: (1, [55], {}),
                            44: (4, [83], {}),
                            116: (
                                7,
                                [89],
                                {
                                    "is_public": False,
                                    "access_group_ids": None,
                                    "inherited_access_group_ids": [8],
                                },
                            ),
                        },
                    ),
                    5: (
                        {
                            "filesize": 300,
                            "create_timestamp": 500,
                        },
                        ("E", "png"),
                        {
                            51: (1, [44, 55, 66], {}),
                            107: (
                                4,
                                [82, 83, 79],
                                {
                                    "is_public": False,
                                    "access_group_ids": [5],
                                    "inherited_access_group_ids": [5],
                                },
                            ),
                            115: (
                                7,
                                [88, 89, 85],
                                {
                                    "is_public": False,
                                    "access_group_ids": [8],
                                    "inherited_access_group_ids": [8],
                                },
                            ),
                        },
                    ),
                },
                "meeting/1": {
                    6: ({}, ("F", "pdf"), {61: (1, [55, 66], {})}),
                    7: ({}, ("G", None), {71: (1, [66], {})}),
                    8: ({}, ("H", None), {81: (1, [], {})}),
                    9: ({}, ("I", None), {91: (1, [], {})}),
                    10: ({}, ("J", "txt"), {101: (1, [44, 55], {})}),
                },
                "meeting/4": {
                    11: (
                        {"filesize": 150},
                        ("F", "pdf"),
                        {
                            102: (
                                4,
                                [83, 79],
                                {
                                    "is_public": False,
                                    "access_group_ids": [5],
                                    "inherited_access_group_ids": [5],
                                },
                            )
                        },
                    ),
                    12: (
                        {"child_ids": [13], "is_directory": True},
                        ("G", None),
                        {
                            103: (
                                4,
                                [79],
                                {
                                    "is_public": False,
                                    "access_group_ids": [5],
                                    "inherited_access_group_ids": [5],
                                },
                            )
                        },
                    ),
                    13: (
                        {"parent_id": 12, "child_ids": [14], "is_directory": True},
                        ("H", None),
                        {
                            104: (
                                4,
                                [],
                                {
                                    "is_public": False,
                                    "access_group_ids": [],
                                    "inherited_access_group_ids": [5],
                                },
                            )
                        },
                    ),
                    14: (
                        {"parent_id": 13, "child_ids": [15], "is_directory": True},
                        ("I", None),
                        {
                            105: (
                                4,
                                [],
                                {
                                    "is_public": False,
                                    "access_group_ids": [],
                                    "inherited_access_group_ids": [5],
                                },
                            )
                        },
                    ),
                    15: (
                        {"parent_id": 14, "filesize": 100},
                        ("J", "txt"),
                        {
                            106: (
                                4,
                                [82, 83],
                                {
                                    "is_public": False,
                                    "access_group_ids": [],
                                    "inherited_access_group_ids": [5],
                                },
                            )
                        },
                    ),
                },
                "meeting/7": {
                    16: (
                        {"filesize": 150},
                        ("F", "pdf"),
                        {
                            108: (
                                7,
                                [89, 85],
                                {
                                    "is_public": False,
                                    "access_group_ids": [8],
                                    "inherited_access_group_ids": [8],
                                },
                            )
                        },
                    ),
                    17: (
                        {"child_ids": [18], "is_directory": True},
                        ("G", None),
                        {
                            109: (
                                7,
                                [85],
                                {
                                    "is_public": False,
                                    "access_group_ids": [8],
                                    "inherited_access_group_ids": [8],
                                },
                            )
                        },
                    ),
                    18: (
                        {"parent_id": 17, "child_ids": [19], "is_directory": True},
                        ("H", None),
                        {
                            110: (
                                7,
                                [],
                                {
                                    "is_public": False,
                                    "access_group_ids": [],
                                    "inherited_access_group_ids": [8],
                                },
                            )
                        },
                    ),
                    19: (
                        {"parent_id": 18, "child_ids": [20], "is_directory": True},
                        ("I", None),
                        {
                            111: (
                                7,
                                [],
                                {
                                    "is_public": False,
                                    "access_group_ids": [],
                                    "inherited_access_group_ids": [8],
                                },
                            )
                        },
                    ),
                    20: (
                        {"parent_id": 19, "filesize": 100},
                        ("J", "txt"),
                        {
                            112: (
                                7,
                                [88, 89],
                                {
                                    "is_public": False,
                                    "access_group_ids": [],
                                    "inherited_access_group_ids": [8],
                                },
                            )
                        },
                    ),
                },
            }
        )

    def test_full_dataset_everywhere_attachments_flag(self) -> None:
        self.create_full_dataset(with_los_related_data=False)

        response = self.request(
            "agenda_item.forward",
            {
                "meeting_ids": [4, 7],
                "agenda_item_ids": [1, 2, 3, 4, 5, 6],
                "with_attachments": True,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_full_dataset([1, 2, 3, 4, 5, 6], [4, 7])
        for collection, id_ in {
            "speaker": 29,
            "structure_level_list_of_speakers": 15,
            "point_of_order_category": 8,
            "structure_level": 21,
            "meeting_user": 18,
        }.items():
            self.assert_model_not_exists(f"{collection}/{id_}")
        self.assert_model_not_exists("group/10")
        self.assert_mediafile_data(
            {
                ONE_ORGANIZATION_FQID: {
                    1: (
                        {
                            "child_ids": [2, 3],
                            "is_directory": True,
                            "create_timestamp": 100,
                        },
                        ("A", None),
                        {},
                    ),
                    2: (
                        {
                            "parent_id": 1,
                            "child_ids": [4],
                            "is_directory": True,
                            "filesize": 100,
                            "create_timestamp": 200,
                        },
                        ("B", None),
                        {
                            21: (1, [66], {}),
                            24: (4, [79], {}),
                            113: (
                                7,
                                [85],
                                {
                                    "is_public": False,
                                    "access_group_ids": None,
                                    "inherited_access_group_ids": [8],
                                },
                            ),
                        },
                    ),
                    3: (
                        {
                            "parent_id": 1,
                            "create_timestamp": 300,
                        },
                        ("C", "txt"),
                        {
                            31: (1, [44, 55, 66], {}),
                            34: (4, [82, 83, 79], {}),
                            114: (
                                7,
                                [88, 89, 85],
                                {
                                    "is_public": False,
                                    "access_group_ids": None,
                                    "inherited_access_group_ids": [8],
                                },
                            ),
                        },
                    ),
                    4: (
                        {
                            "parent_id": 2,
                            "filesize": 200,
                            "create_timestamp": 400,
                        },
                        ("D", "png"),
                        {
                            41: (1, [55], {}),
                            44: (4, [83], {}),
                            116: (
                                7,
                                [89],
                                {
                                    "is_public": False,
                                    "access_group_ids": None,
                                    "inherited_access_group_ids": [8],
                                },
                            ),
                        },
                    ),
                    5: (
                        {
                            "filesize": 300,
                            "create_timestamp": 500,
                        },
                        ("E", "png"),
                        {
                            51: (1, [44, 55, 66], {}),
                            107: (
                                4,
                                [82, 83, 79],
                                {
                                    "is_public": False,
                                    "access_group_ids": [5],
                                    "inherited_access_group_ids": [5],
                                },
                            ),
                            115: (
                                7,
                                [88, 89, 85],
                                {
                                    "is_public": False,
                                    "access_group_ids": [8],
                                    "inherited_access_group_ids": [8],
                                },
                            ),
                        },
                    ),
                },
                "meeting/1": {
                    6: ({}, ("F", "pdf"), {61: (1, [55, 66], {})}),
                    7: ({}, ("G", None), {71: (1, [66], {})}),
                    8: ({}, ("H", None), {81: (1, [], {})}),
                    9: ({}, ("I", None), {91: (1, [], {})}),
                    10: ({}, ("J", "txt"), {101: (1, [44, 55], {})}),
                },
                "meeting/4": {
                    11: (
                        {"filesize": 150},
                        ("F", "pdf"),
                        {
                            102: (
                                4,
                                [83, 79],
                                {
                                    "is_public": False,
                                    "access_group_ids": [5],
                                    "inherited_access_group_ids": [5],
                                },
                            )
                        },
                    ),
                    12: (
                        {"child_ids": [13], "is_directory": True},
                        ("G", None),
                        {
                            103: (
                                4,
                                [79],
                                {
                                    "is_public": False,
                                    "access_group_ids": [5],
                                    "inherited_access_group_ids": [5],
                                },
                            )
                        },
                    ),
                    13: (
                        {"parent_id": 12, "child_ids": [14], "is_directory": True},
                        ("H", None),
                        {
                            104: (
                                4,
                                [],
                                {
                                    "is_public": False,
                                    "access_group_ids": [],
                                    "inherited_access_group_ids": [5],
                                },
                            )
                        },
                    ),
                    14: (
                        {"parent_id": 13, "child_ids": [15], "is_directory": True},
                        ("I", None),
                        {
                            105: (
                                4,
                                [],
                                {
                                    "is_public": False,
                                    "access_group_ids": [],
                                    "inherited_access_group_ids": [5],
                                },
                            )
                        },
                    ),
                    15: (
                        {"parent_id": 14, "filesize": 100},
                        ("J", "txt"),
                        {
                            106: (
                                4,
                                [82, 83],
                                {
                                    "is_public": False,
                                    "access_group_ids": [],
                                    "inherited_access_group_ids": [5],
                                },
                            )
                        },
                    ),
                },
                "meeting/7": {
                    16: (
                        {"filesize": 150},
                        ("F", "pdf"),
                        {
                            108: (
                                7,
                                [89, 85],
                                {
                                    "is_public": False,
                                    "access_group_ids": [8],
                                    "inherited_access_group_ids": [8],
                                },
                            )
                        },
                    ),
                    17: (
                        {"child_ids": [18], "is_directory": True},
                        ("G", None),
                        {
                            109: (
                                7,
                                [85],
                                {
                                    "is_public": False,
                                    "access_group_ids": [8],
                                    "inherited_access_group_ids": [8],
                                },
                            )
                        },
                    ),
                    18: (
                        {"parent_id": 17, "child_ids": [19], "is_directory": True},
                        ("H", None),
                        {
                            110: (
                                7,
                                [],
                                {
                                    "is_public": False,
                                    "access_group_ids": [],
                                    "inherited_access_group_ids": [8],
                                },
                            )
                        },
                    ),
                    19: (
                        {"parent_id": 18, "child_ids": [20], "is_directory": True},
                        ("I", None),
                        {
                            111: (
                                7,
                                [],
                                {
                                    "is_public": False,
                                    "access_group_ids": [],
                                    "inherited_access_group_ids": [8],
                                },
                            )
                        },
                    ),
                    20: (
                        {"parent_id": 19, "filesize": 100},
                        ("J", "txt"),
                        {
                            112: (
                                7,
                                [88, 89],
                                {
                                    "is_public": False,
                                    "access_group_ids": [],
                                    "inherited_access_group_ids": [8],
                                },
                            )
                        },
                    ),
                },
            }
        )

    def test_full_dataset_everywhere_moderator_notes_flag(self) -> None:
        self.create_full_dataset(with_mediafiles=False)

        response = self.request(
            "agenda_item.forward",
            {
                "meeting_ids": [4, 7],
                "agenda_item_ids": [1, 2, 3, 4, 5, 6],
                "with_moderator_notes": True,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_full_dataset([1, 2, 3, 4, 5, 6], [4, 7], with_moderator_notes=True)
        for collection, id_ in {
            "mediafile": 11,
            "meeting_mediafile": 102,
            "speaker": 29,
            "structure_level_list_of_speakers": 15,
            "point_of_order_category": 8,
            "structure_level": 21,
            "meeting_user": 18,
        }.items():
            self.assert_model_not_exists(f"{collection}/{id_}")
        self.assert_model_not_exists("group/10")

    def test_full_dataset_everywhere_speaker_flag(self) -> None:
        self.set_models(
            {
                "meeting/4": {"list_of_speakers_default_structure_level_time": 60},
                "meeting/7": {"list_of_speakers_default_structure_level_time": 60},
            }
        )
        self.create_full_dataset(with_mediafiles=False)

        response = self.request(
            "agenda_item.forward",
            {
                "meeting_ids": [4, 7],
                "agenda_item_ids": [1, 2, 3, 4, 5, 6],
                "with_speakers": True,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_full_dataset([1, 2, 3, 4, 5, 6], [4, 7], with_speakers=True)
        for collection, id_ in {
            "mediafile": 11,
            "meeting_mediafile": 102,
        }.items():
            self.assert_model_not_exists(f"{collection}/{id_}")
        self.assert_group_data(
            {
                4: {10: "Delegate"},
                7: {
                    11: "Default",
                    12: "Admin",
                    13: "Delegate",
                },
            }
        )
        meeting_to_old_to_new_structure_level_id: dict[int, dict[int, int]] = {
            4: {
                1: 13,
                2: 14,
                3: 21,
                4: 15,
                5: 22,
                6: 23,
                7: 24,
                8: 25,
                9: 26,
                10: 27,
                11: 28,
                12: 29,
            },
            7: {id_: id_ + 29 for id_ in range(1, 13)},
        }
        self.assert_structure_level_data(
            {
                4: {
                    13: ("red", None),
                    14: ("orange", "#ff8000"),
                    15: ("green", "#00ff33"),
                    16: ("ocean", "#0000ff"),
                    17: ("whitecat", "#ffffff"),
                    18: ("greycat", "#808080"),
                    19: ("blackcat", "#000000"),
                    20: ("void", None),
                    21: ("yellow", "#ffff00"),
                    22: ("cyan", "#00ffff"),
                    23: ("blue", "#0000ff"),
                    24: ("pink", "#ff00ff"),
                    25: ("purple", "#8000ff"),
                    26: ("white", "#ffffff"),
                    27: ("grey", "#808080"),
                    28: ("black", "#000000"),
                    29: ("nothing", None),
                },
                7: {
                    30: ("red", "#ff0000"),
                    31: ("orange", "#ff8000"),
                    32: ("yellow", "#ffff00"),
                    33: ("green", "#00ff00"),
                    34: ("cyan", "#00ffff"),
                    35: ("blue", "#0000ff"),
                    36: ("pink", "#ff00ff"),
                    37: ("purple", "#8000ff"),
                    38: ("white", "#ffffff"),
                    39: ("grey", "#808080"),
                    40: ("black", "#000000"),
                    41: ("nothing", None),
                },
            }
        )

        def get_meeting_user_data(id_: int) -> dict[str, str | None]:
            return {
                field: (val if len(field) - 6 != id_ % 3 else None)
                for field, val in [
                    ("number", f"MTNGUSR{id_}"),
                    ("comment", f"Comment of meeting user{id_}"),
                    ("about_me", f"I am meeting user {id_}"),
                ]
            }

        meeting_id_to_old_to_new_muser_id: dict[int, dict[int, int]] = {
            4: {
                1: 2,
                4: 18,
                5: 19,
                6: 20,
                7: 21,
                8: 22,
                9: 10,
                11: 12,
                13: 14,
                16: 17,
            },
            7: {
                1: 3,
                4: 23,
                5: 24,
                6: 25,
                7: 26,
                8: 27,
                9: 28,
                11: 29,
                13: 15,
                16: 30,
            },
        }
        self.assert_meeting_user_data(
            {
                4: {
                    2: (1, [4, 5], [17], get_meeting_user_data(2)),  # Take 4 add 5
                    18: (2, [4], [13], get_meeting_user_data(4)),  # From meeting_user 4
                    19: (3, [5], [14], get_meeting_user_data(5)),  # From meeting_user 5
                    20: (
                        4,
                        [10],
                        [21],
                        get_meeting_user_data(6),
                    ),  # From meeting_user 6
                    21: (
                        5,
                        [4, 5],
                        [29],
                        get_meeting_user_data(7),
                    ),  # From meeting_user 7
                    22: (
                        6,
                        [5, 10],
                        [14, 15, 23, 25, 27, 29],
                        get_meeting_user_data(8),
                    ),  # From meeting_user 8
                    10: (
                        7,
                        [4, 10],
                        [13, 14, 15],
                        get_meeting_user_data(10),
                    ),  # Take 4 add 10
                    12: (
                        8,
                        [5],
                        [16, 17, 18, 19, 20],
                        get_meeting_user_data(12),
                    ),  # Take 5
                    14: (9, [6, 10], [], get_meeting_user_data(14)),  # Take 6 add 10
                    17: (
                        10,
                        [4, 5],
                        [14, 16, 18, 20],
                        get_meeting_user_data(17),
                    ),  # Take 4 add 5
                },
                7: {
                    3: (
                        1,
                        [8, 9, 12],
                        None,
                        get_meeting_user_data(3),
                    ),  # Take 8, 9 add 12
                    23: (
                        2,
                        [11],
                        [30],
                        get_meeting_user_data(4),
                    ),  # From meeting_user 4
                    24: (
                        3,
                        [12],
                        [31],
                        get_meeting_user_data(5),
                    ),  # From meeting_user 5
                    25: (
                        4,
                        [13],
                        [32],
                        get_meeting_user_data(6),
                    ),  # From meeting_user 6
                    26: (
                        5,
                        [11, 12],
                        [41],
                        get_meeting_user_data(7),
                    ),  # From meeting_user 7
                    27: (
                        6,
                        [12, 13],
                        [31, 33, 35, 37, 39, 41],
                        get_meeting_user_data(8),
                    ),  # From meeting_user 8
                    28: (
                        7,
                        [13],
                        [30, 32, 34, 36, 38, 40],
                        get_meeting_user_data(9),
                    ),  # From meeting_user 9
                    29: (
                        8,
                        [12],
                        [],
                        get_meeting_user_data(11),
                    ),  # From meeting_user 11
                    15: (9, [9, 13], None, get_meeting_user_data(15)),  # Take 9 add 13
                    30: (
                        10,
                        [11, 12],
                        list(range(30, 42)),
                        get_meeting_user_data(16),
                    ),  # From meeting_user 16
                },
            }
        )
        meeting_to_old_to_new_speaker_id = {
            4: {old_id: old_id + 28 for old_id in range(1, 29)},
            7: {old_id: old_id + 56 for old_id in range(1, 29)},
        }
        # {meeting_id -> {los_id -> (speaker_id, SpeakerData)[]}}
        self.assert_speaker_data(
            {
                4: {
                    771: list(
                        enumerate(EXAMPLE_LOS_DATA[0], 29)
                    ),  # 110, speaker 1-4 -> 29-32
                    773: list(
                        enumerate(EXAMPLE_LOS_DATA[1], 33)
                    ),  # 220, speaker 5-9 -> 33-37
                    774: list(
                        enumerate(EXAMPLE_LOS_DATA[2], 38)
                    ),  # 330, speaker 10-19 -> 38-47
                    775: list(
                        enumerate(EXAMPLE_LOS_DATA[3], 48)
                    ),  # 440, speaker 20-22 -> 48-50
                    776: list(
                        enumerate(EXAMPLE_LOS_DATA[4], 51)
                    ),  # 550, speaker 23-28 -> 51-56
                },
                7: {
                    777: list(
                        enumerate(EXAMPLE_LOS_DATA[0], 57)
                    ),  # 110, speaker 1-4 -> 57-60
                    779: list(
                        enumerate(EXAMPLE_LOS_DATA[1], 61)
                    ),  # 220, speaker 5-9 -> 61-65
                    780: list(
                        enumerate(EXAMPLE_LOS_DATA[2], 66)
                    ),  # 330, speaker 10-19 -> 66-75
                    781: list(
                        enumerate(EXAMPLE_LOS_DATA[3], 76)
                    ),  # 440, speaker 20-22 -> 76-78
                    782: list(
                        enumerate(EXAMPLE_LOS_DATA[4], 79)
                    ),  # 550, speaker 23-28 -> 79-84
                },
            },
            meeting_id_to_old_to_new_muser_id,
        )
        next_sllos_id = sum(len(sllos) for sllos in EXAMPLE_SLLOS_DATA) + 1
        self.assert_sllos_data(
            {
                4: {
                    774: list(enumerate(EXAMPLE_SLLOS_DATA[0], next_sllos_id)),
                    775: list(enumerate(EXAMPLE_SLLOS_DATA[1], next_sllos_id + 7)),
                    776: list(enumerate(EXAMPLE_SLLOS_DATA[2], next_sllos_id + 9)),
                },
                7: {
                    780: list(enumerate(EXAMPLE_SLLOS_DATA[0], next_sllos_id + 14)),
                    781: list(enumerate(EXAMPLE_SLLOS_DATA[1], next_sllos_id + 21)),
                    782: list(enumerate(EXAMPLE_SLLOS_DATA[2], next_sllos_id + 23)),
                },
            },
            meeting_to_old_to_new_structure_level_id,
            meeting_to_old_to_new_speaker_id,
        )
        self.assert_pooc_data(
            {
                4: {
                    4: ("You have", 1, []),
                    5: ("A point", 2, [37]),
                    6: ("A", 3, []),
                    7: ("Small point", 4, [50]),
                    8: ("Big point", 1, [36, 48, 49]),  # new
                },
                7: {
                    9: ("Big point", 1, [64, 76, 77]),  # new
                    10: ("A point", 2, [65]),  # new
                    11: ("Small point", 3, [78]),  # new
                },
            }
        )

    # TODO: Test with smaller more specific subcases of the dataset
    # TODO: Test edge cases, permissions and errors
