from datastore.shared.util.otel import *

from opentelemetry.instrumentation.requests import RequestsInstrumentor

def instrument_requests():
    RequestsInstrumentor().instrument()
