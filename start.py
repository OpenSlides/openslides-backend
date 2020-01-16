import os

from werkzeug.serving import run_simple

from openslides_backend.actions.http.application import create_application

application = create_application()


def main() -> None:
    """
    Main entry point for this start script.
    """
    # TODO: Log "Start Werkzeug's development server" here.
    os.environ.setdefault("OPENSLIDES_BACKEND_DEBUG", "1")
    run_simple("localhost", 8000, application, use_reloader=True)


if __name__ == "__main__":
    main()
