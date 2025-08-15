from enum import Enum


class SpeechState(str, Enum):
    CONTRIBUTION = "contribution"
    PRO = "pro"
    CONTRA = "contra"
    INTERVENTION = "intervention"
    INTERVENTION_ANSWER = "intervention_answer"
    INTERPOSED_QUESTION = "interposed_question"
