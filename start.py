from werkzeug.serving import run_simple

from openslides_backend.core import create_application

application = create_application()


def main() -> None:
    """
    Main entry point for this start script.
    """
    # Log "Start Werkzeug's development server."
    run_simple("localhost", 8000, application, use_reloader=True)


if __name__ == "__main__":
    main()
