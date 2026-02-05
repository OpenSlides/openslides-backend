import logging
import os
import sys

from datastore.reader.app import register_services

from openslides_backend.presenter.check_database import check_meetings
from openslides_backend.presenter.check_database_all import check_everything
from openslides_backend.shared.env import Environment
from openslides_backend.wsgi import OpenSlidesBackendServices

from json import dumps


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

    print(dumps(everything))

    return 0


if __name__ == "__main__":
    sys.exit(main())
