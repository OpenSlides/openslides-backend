class MockGunicornThreadWorker:
    class Tmp:
        @staticmethod
        def notify() -> None:
            pass

    tmp = Tmp()
