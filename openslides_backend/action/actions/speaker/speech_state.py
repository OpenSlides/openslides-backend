from enum import StrEnum


class SpeechState(StrEnum):
    CONTRIBUTION = "contribution"
    PRO = "pro"
    CONTRA = "contra"
    INTERVENTION = "intervention"
    INTERPOSED_QUESTION = "interposed_question"
