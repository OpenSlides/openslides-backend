from typing import Optional

from openslides_backend.models.models import Poll

from ....shared.exceptions import ActionException


def base_check_onehundred_percent_base(
    pollmethod: Optional[str], onehundred_percent_base: Optional[str]
) -> None:
    error_msg = "This onehundred_percent_base not allowed in this pollmethod."
    if pollmethod == "Y" and onehundred_percent_base in (
        Poll.ONEHUNDRED_PERCENT_BASE_N,
        Poll.ONEHUNDRED_PERCENT_BASE_YN,
        Poll.ONEHUNDRED_PERCENT_BASE_YNA,
    ):
        raise ActionException(error_msg)
    elif pollmethod == "N" and onehundred_percent_base in (
        Poll.ONEHUNDRED_PERCENT_BASE_Y,
        Poll.ONEHUNDRED_PERCENT_BASE_YN,
        Poll.ONEHUNDRED_PERCENT_BASE_YNA,
    ):
        raise ActionException(error_msg)
    elif (
        pollmethod == "YN"
        and onehundred_percent_base == Poll.ONEHUNDRED_PERCENT_BASE_YNA
    ):
        raise ActionException(error_msg)
