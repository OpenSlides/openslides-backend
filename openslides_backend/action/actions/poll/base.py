from typing import Optional

from ....shared.exceptions import ActionException


def base_check_onehundred_percent_base(
    pollmethod: Optional[str], onehundred_percent_base: Optional[str]
) -> None:
    error_msg = "This onehundred_percent_base not allowed in this pollmethod."
    if pollmethod == "Y" and onehundred_percent_base in ("N", "YN", "YNA"):
        raise ActionException(error_msg)
    elif pollmethod == "N" and onehundred_percent_base in ("Y", "YN", "YNA"):
        raise ActionException(error_msg)
    elif pollmethod == "YN" and onehundred_percent_base == "YNA":
        raise ActionException(error_msg)
