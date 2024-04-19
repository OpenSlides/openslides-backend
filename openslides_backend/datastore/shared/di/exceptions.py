class DependencyInjectionError(Exception):
    pass


class DependencyNotFound(DependencyInjectionError):
    def __init__(self, protocol):
        self.protocol = protocol
