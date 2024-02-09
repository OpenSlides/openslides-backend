import os

from .shared.env import Environment
from .shared.otel import init as otel_init
from .shared.otel import instrument_requests as otel_instrument_requests

otel_init(Environment(os.environ), "backend")
otel_instrument_requests()
