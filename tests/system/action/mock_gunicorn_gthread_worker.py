class MockGunicornThreadWorker(object):
    class Tmp:
        @staticmethod
        def notify() -> None:
            pass

    tmp = Tmp()
