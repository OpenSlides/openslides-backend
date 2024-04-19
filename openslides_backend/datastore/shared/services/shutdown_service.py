from openslides_backend.datastore.shared.di import service_as_singleton


@service_as_singleton
class ShutdownService:
    def __init__(self):
        self.instances = []

    def register(self, instance):
        self.instances.append(instance)

    def shutdown(self):
        for instance in self.instances:
            self.shutdown_instance(instance)

    def shutdown_instance(self, instance):
        handler = getattr(instance, "shutdown", None)
        if callable(handler):
            self.call_shutdown_handler(handler)

    def call_shutdown_handler(self, handler):
        try:
            handler()
        except:  # noqa
            # TODO: logging
            pass  # ignore every errors during cleanup
