import mimetypes


def add_mimetypes() -> None:
    """
    for mimetypes we use the mimetypes of the current python version.
    If we miss some, we could add them here.
    """
    mimetypes.add_type("font/ttf", ".ttf")
    mimetypes.add_type("font/otf", ".otf")
    mimetypes.add_type("application/x-7z-compressed", ".7z")
    mimetypes.add_type("application/vnd.oasis.opendocument.text", ".odt")
    mimetypes.add_type("application/vnd.oasis.opendocument.spreadsheet", ".ods")
