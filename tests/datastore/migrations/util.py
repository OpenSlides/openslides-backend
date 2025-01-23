from unittest.mock import MagicMock


class LogMock(MagicMock):
    @property
    def output(self) -> tuple[str, ...]:
        return tuple(c[0][0] for c in self.call_args_list)
