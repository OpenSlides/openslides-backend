from enum import Enum


class SpeechState(str, Enum):
    CONTRIBUTION = "contribution"
    PRO = "pro"
    CONTRA = "contra"
    INTERVENTION = "intervention"
    INTERPOSED_QUESTION = "interposed_question"
