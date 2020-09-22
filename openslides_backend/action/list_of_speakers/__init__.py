from ..action import register_action
from ..base import DummyAction
from . import update  # noqa


@register_action("list_of_speakers.manage_speakers")
class ListOfSpeakersManageSpeakers(DummyAction):
    pass


@register_action("list_of_speakers.speak")
class ListOfSpeakersSpeak(DummyAction):
    pass


@register_action("list_of_speakers.mark_speaker")
class ListOfSpeakersMarkSpeaker(DummyAction):
    pass


@register_action("list_of_speakers.stop_current_speaker")
class ListOfSpeakersStopCurrentSpeaker(DummyAction):
    pass


@register_action("list_of_speakers.sort")
class ListOfSpeakersSort(DummyAction):
    pass


@register_action("list_of_speakers.re_add_last")
class ListOfSpeakersReAddLast(DummyAction):
    pass


@register_action("list_of_speakers.prune")
class ListOfSpeakersPrune(DummyAction):
    pass


@register_action("list_of_speakers.delete_all_speakers_of_all_lists")
class ListOfSpeakersDeleteAllSpeakersOfAllLists(DummyAction):
    pass
