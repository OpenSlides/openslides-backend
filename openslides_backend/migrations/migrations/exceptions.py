class MigrationException(Exception):
    def __init__(self, errors: list[str]):
        err_str = '\n* '.join(errors)
        super().__init__(f"Migration exception:\n* {err_str}")