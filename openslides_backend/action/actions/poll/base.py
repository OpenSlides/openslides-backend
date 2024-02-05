from ....shared.exceptions import ActionException


def base_check_onehundred_percent_base(
    pollmethod: str | None, onehundred_percent_base: str | None
) -> None:
    error_msg = "This onehundred_percent_base not allowed in this pollmethod."
    if pollmethod == "Y" and onehundred_percent_base in ("N", "YN", "YNA"):
        raise ActionException(error_msg)
    elif pollmethod == "N" and onehundred_percent_base in ("Y", "YN", "YNA"):
        raise ActionException(error_msg)
    elif pollmethod == "YN" and onehundred_percent_base == "YNA":
        raise ActionException(error_msg)
