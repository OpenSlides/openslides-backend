from contextlib import nullcontext
from typing import Any, Dict, Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from .interfaces.env import Env

otel_initialized = False


def init(env: Env, service_name: str) -> None:
    """
    Initializes the opentelemetry components and connection to the otel collector.
    """
    if not env.is_otel_enabled():
        return
    span_exporter = OTLPSpanExporter(
        endpoint="http://collector:4317",
        insecure=True,
        # optional
        # credentials=ChannelCredentials(credentials),
        # headers=(("metadata", "metadata")),
    )
    tracer_provider = TracerProvider(
        resource=Resource.create({SERVICE_NAME: service_name})
    )
    trace.set_tracer_provider(tracer_provider)
    span_processor = BatchSpanProcessor(span_exporter)
    tracer_provider.add_span_processor(span_processor)
    global otel_initialized
    otel_initialized = True


def instrument_requests() -> None:
    RequestsInstrumentor().instrument()


def make_span(env: Env, name: str, attributes: Optional[Dict[str, str]] = None) -> Any:
    """
    Returns a new child span to the currently active span.
    If OPENTELEMETRY_ENABLED is not truthy a nullcontext will be returned instead.
    So at any point in the code this function can be called in a with statement
    without any additional checking needed.

    Example:
    ```
    with make_span("foo") as span:
        ...
        with make_span("bar") as subspan:
            ...
    ```
    """
    if not env.is_otel_enabled():
        return nullcontext()

    # global otel_initialized
    # assert (
    #     otel_initialized
    # ), "backend:Opentelemetry span to be set before having set a TRACER_PROVIDER"

    tracer = trace.get_tracer_provider().get_tracer(__name__)
    span = tracer.start_as_current_span(name, attributes=attributes)

    return span
