import logging
import os
import sys
from json import dumps

from datastore.reader.app import register_services

from openslides_backend.shared.env import Environment
from openslides_backend.wsgi import OpenSlidesBackendServices


def main() -> int:
    register_services()
    env = Environment(os.environ)
    services = OpenSlidesBackendServices(
        config=env.get_service_url(),
        logging=logging,
        env=env,
    )
    datastore = services.datastore()

    everything = datastore.get_everything()
    print(dumps(everything, indent=4, sort_keys=True, default=str))

    return 0


if __name__ == "__main__":
    sys.exit(main())
