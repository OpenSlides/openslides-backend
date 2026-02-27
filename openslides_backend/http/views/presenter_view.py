from ...migrations.migration_helper import MigrationHelper
from ...presenter.presenter import PresenterHandler
from ...services.postgresql.db_connection_handling import get_new_os_conn
from ...shared.interfaces.wsgi import RouteResponse
from ..request import Request
from .base_view import BaseView, route


class PresenterView(BaseView):
    """
    The PresenterView receives a bundle of presentations via HTTP and handles
    it to the PresenterHandler.
    """

    method = "POST"

    @route("handle_request")
    def presenter_route(self, request: Request) -> RouteResponse:
        self.logger.debug("Start dispatching presenter request.")

        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                MigrationHelper.assert_migration_index(curs)

        # Get user id.
        user_id, access_token = self.get_user_id_from_headers(
            request.headers, request.cookies
        )

        # Handle request.
        handler = PresenterHandler(
            env=self.env,
            logging=self.logging,
            services=self.services,
        )
        presenter_response = handler.handle_request(request, user_id)

        # Finish request.
        self.logger.debug("Presenter request finished successfully. Send response now.")
        return presenter_response, access_token

    @route("theme", method="GET", json=False)
    def theme_route(self, request: Request) -> RouteResponse:
        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "SELECT theme_id FROM organization_t WHERE id = 1"
                )
                row = curs.fetchone()
                if not row or not row["theme_id"]:
                    from ..http_exceptions import NotFound

                    raise NotFound()

                theme_id = row["theme_id"]

                color_fields = [
                    "primary_50", "primary_100", "primary_200", "primary_300",
                    "primary_400", "primary_500", "primary_600", "primary_700",
                    "primary_800", "primary_900",
                    "primary_a100", "primary_a200", "primary_a400", "primary_a700",
                    "accent_50", "accent_100", "accent_200", "accent_300",
                    "accent_400", "accent_500", "accent_600", "accent_700",
                    "accent_800", "accent_900",
                    "accent_a100", "accent_a200", "accent_a400", "accent_a700",
                    "warn_50", "warn_100", "warn_200", "warn_300",
                    "warn_400", "warn_500", "warn_600", "warn_700",
                    "warn_800", "warn_900",
                    "warn_a100", "warn_a200", "warn_a400", "warn_a700",
                    "headbar", "yes", "no", "abstain",
                ]
                columns = ", ".join(color_fields)
                curs.execute(
                    f"SELECT {columns} FROM theme_t WHERE id = %s",
                    (theme_id,),
                )
                theme_row = curs.fetchone()
                if not theme_row:
                    from ..http_exceptions import NotFound

                    raise NotFound()

                result = {
                    k: v for k, v in theme_row.items() if v is not None
                }
        return result, None

    @route("health", method="GET", json=False)
    def health_route(self, request: Request) -> RouteResponse:
        return {"status": "running"}, None
