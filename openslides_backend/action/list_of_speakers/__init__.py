from ..action import register_action
from ..base import DummyAction


@register_action("list_of_speakers.create")
class ListOfSpeakersCreate(DummyAction):
    pass


@register_action("list_of_speakers.update")
class ListOfSpeakersUpdate(DummyAction):
    pass


@register_action("list_of_speakers.delete")
class ListOfSpeakersDelete(DummyAction):
    pass


@register_action("list_of_speakers.manage_speakers")
class ListOfSpeakersManageSpeakers(DummyAction):
    pass


@register_action("list_of_speakers.speak")
class ListOfSpeakersSpeak(DummyAction):
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
