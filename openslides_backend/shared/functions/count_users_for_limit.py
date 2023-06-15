from ...services.datastore.interface import DatastoreService
from ..filters import FilterOperator


def count_users_for_limit(datastore: DatastoreService) -> int:
    """Counts the users with special conditions to compare with
    limit_of_users."""
    filter_ = FilterOperator("is_active", "=", True)
    count_of_users = datastore.count("user", filter_)
    return count_of_users
