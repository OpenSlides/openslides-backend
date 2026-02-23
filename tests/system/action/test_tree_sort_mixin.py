import threading
from typing import Any

import pytest

from tests.system.action.base import BaseActionTestCase

CategoryStructure = list[tuple[int, "CategoryStructure"]]


class TestTreeSortMixin(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(1)

    def get_motion_category_data(
        self,
        structure: CategoryStructure,
        meeting_id: int = 1,
        level: int = 0,
        previous_data: list[tuple[str, dict[str, Any]]] = [],
        parent_id: int | None = None,
    ) -> dict[str, dict[str, Any]]:
        data: dict[str, dict[str, Any]] = {}
        for id_, children in structure:
            weight = previous_data[-1][1]["weight"] + 1 if previous_data else 0
            fqid = f"motion_category/{id_}"
            date = {
                "name": f"Category {id_}",
                "weight": weight,
                "level": level,
                "parent_id": parent_id,
                "meeting_id": meeting_id,
            }
            previous_data.append((fqid, date))
            data[fqid] = date
            data.update(
                self.get_motion_category_data(
                    children, meeting_id, level + 1, previous_data, id_
                )
            )
        return data

    def set_mass_test_data(self) -> None:
        self.set_models(
            self.get_motion_category_data(
                [
                    (base, [(base + 1, [(base + 2, [])]), (base + 3, [])])
                    for base in range(1, 101, 4)
                ]
            )
        )

    @pytest.mark.skip(
        "TODO: unskip later. Currently runs into 'Unexpected error reading from database: could not serialize access due to concurrent update' error."
    )
    def test_sort_and_delete_at_once(self) -> None:
        self.set_mass_test_data()
        sort_thread = threading.Thread(target=self.thread_sort_method)
        sort_thread.start()
        delete_thread = threading.Thread(
            target=self.thread_delete_method, kwargs={"id_": 5}
        )
        delete_thread.start()
        sort_thread.join()
        delete_thread.join()
        self.assert_sort_thread_results()
        self.assert_delete_thread_results(5)

    @pytest.mark.skip(
        "TODO: unskip later. Currently runs into 'Unexpected error reading from database: could not serialize access due to concurrent update' error during a database request with raise_exception=False, which then crashes the transaction (SingleRelationHandler ln. 134)."
    )
    def test_sort_and_create_at_once(self) -> None:
        self.set_mass_test_data()
        sort_thread = threading.Thread(target=self.thread_sort_method)
        sort_thread.start()
        create_thread = threading.Thread(
            target=self.thread_create_method, kwargs={"name": "TIM", "parent_id": 42}
        )
        create_thread.start()
        sort_thread.join()
        create_thread.join()
        self.assert_sort_thread_results()
        self.assert_create_thread_results("TIM", 42)

    @pytest.mark.skip(
        "TODO: unskip later. Currently runs into 'Unexpected error reading from database: could not serialize access due to concurrent update' error."
    )
    def test_sort_and_delete_at_once_reverse(self) -> None:
        self.set_mass_test_data()
        delete_thread = threading.Thread(
            target=self.thread_delete_method, kwargs={"id_": 5}
        )
        delete_thread.start()
        sort_thread = threading.Thread(target=self.thread_sort_method)
        sort_thread.start()
        delete_thread.join()
        sort_thread.join()
        self.assert_delete_thread_results(5)
        self.assert_sort_thread_results()

    @pytest.mark.skip(
        "TODO: unskip later. Currently runs into 'Unexpected error reading from database: could not serialize access due to concurrent update' error during a database request with raise_exception=False, which then crashes the transaction (SingleRelationHandler ln. 134)."
    )
    def test_sort_and_create_at_once_reverse(self) -> None:
        self.set_mass_test_data()
        create_thread = threading.Thread(
            target=self.thread_create_method, kwargs={"name": "TIM", "parent_id": 42}
        )
        create_thread.start()
        sort_thread = threading.Thread(target=self.thread_sort_method)
        sort_thread.start()
        create_thread.join()
        sort_thread.join()
        self.assert_create_thread_results("TIM", 42)
        self.assert_sort_thread_results()

    def thread_sort_method(self) -> None:
        self.sort_response = self.request(
            "motion_category.sort",
            {
                "meeting_id": 1,
                "tree": [
                    {
                        "id": base,
                        "children": [
                            {"id": base + 1, "children": [{"id": base + 2}]},
                            {"id": base + 3},
                            {"id": base + 4},
                        ],
                    }
                    for base in range(1, 101, 5)
                ],
            },
        )

    def assert_sort_thread_results(self, expect_error: bool = False) -> None:
        if expect_error:
            self.assert_status_code(self.sort_response, 400)
        else:
            assert self.sort_response.json == {
                "message": "Actions handled successfully",
                "results": [None],
                "status_code": 200,
                "success": True,
            }

    def thread_delete_method(self, id_: int) -> None:
        self.delete_response = self.request("motion_category.delete", {"id": id_})

    def assert_delete_thread_results(
        self, id_: int, expect_error: bool = False
    ) -> None:
        if expect_error:
            self.assert_status_code(self.delete_response, 400)
        else:
            assert self.delete_response.json == {
                "message": "Actions handled successfully",
                "results": [[None]],
                "status_code": 200,
                "success": True,
            }
            self.assert_model_not_exists(f"motion_category/{id_}")

    def thread_create_method(self, name: str, parent_id: int | None = None) -> None:
        self.create_response = self.request(
            "motion_category.create",
            {"meeting_id": 1, "name": name, "parent_id": parent_id},
        )

    def assert_create_thread_results(
        self, name: str, parent_id: int | None = None, expect_error: bool = False
    ) -> None:
        if expect_error:
            self.assert_status_code(self.create_response, 400)
        else:
            assert self.create_response.json == {
                "message": "Actions handled successfully",
                "results": [[{"id": 101}]],
                "status_code": 200,
                "success": True,
            }
            self.assert_model_exists(
                "motion_category/101",
                {"meeting_id": 1, "name": name, "parent_id": parent_id},
            )
