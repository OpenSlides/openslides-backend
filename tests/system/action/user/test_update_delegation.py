from tests.system.action.base import BaseActionTestCase


class UserUpdateDelegationActionTest(BaseActionTestCase):
    def setup_vote_delegation(self) -> None:
        self.set_models(
            {
                "meeting/222": {"name": "Meeting222"},
                "meeting/223": {"name": "Meeting223"},
                "group/1": {"meeting_id": 222, "user_ids": [1, 2, 3, 4]},
                "group/100": {"meeting_id": 223, "user_ids": [5]},
                "user/1": {
                    "group_$_ids": ["222"],
                    "group_$222_ids": [1],
                },
                "user/2": {
                    "username": "voter",
                    "group_$_ids": ["222"],
                    "group_$222_ids": [1],
                    "vote_delegations_$222_from_ids": [3, 4],
                    "vote_delegations_$_from_ids": ["222"],
                },
                "user/3": {
                    "username": "delegator1",
                    "group_$_ids": ["222"],
                    "group_$222_ids": [1],
                    "vote_delegated_$222_to_id": 2,
                    "vote_delegated_$_to_id": ["222"],
                },
                "user/4": {
                    "username": "delegator2",
                    "group_$_ids": ["222"],
                    "group_$222_ids": [1],
                    "vote_delegated_$222_to_id": 2,
                    "vote_delegated_$_to_id": ["222"],
                },
                "user/5": {
                    "username": "user5",
                    "group_$_ids": ["223"],
                    "group_$223_ids": [100],
                },
            }
        )

    def test_update_simple_delegated_to(self) -> None:
        """ user/2 with permission delegates to admin user/1 """
        self.set_models(
            {
                "meeting/222": {"name": "Meeting222"},
                "group/1": {"meeting_id": 222, "user_ids": [1, 2]},
                "user/1": {
                    "group_$_ids": ["222"],
                    "group_$222_ids": [1],
                },
                "user/2": {
                    "group_$_ids": ["222"],
                    "group_$222_ids": [1],
                },
            }
        )

        response = self.request(
            "user.update",
            {
                "id": 2,
                "vote_delegated_$_to_id": {222: 1},
            }
            # test_update_vote_delegation
            # reverse("user-detail", args=[user.pk]),
            # {"vote_delegated_to_id": self.admin.pk},
        )

        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1",
            {
                "vote_delegations_$222_from_ids": [2],
                "vote_delegations_$_from_ids": ["222"],
            },
        )
        self.assert_model_exists(
            "user/2",
            {"vote_delegated_$222_to_id": 1, "vote_delegated_$_to_id": ["222"]},
        )

    def test_update_vote_delegated_to_self(self) -> None:
        """ user/1 tries to delegate to himself """
        self.set_models(
            {
                "meeting/222": {"name": "Meeting222"},
                "group/1": {"meeting_id": 222, "user_ids": [1]},
                "user/1": {
                    "group_$_ids": ["222"],
                    "group_$222_ids": [1],
                },
            },
        )
        response = self.request(
            "user.update",
            {
                "id": 1,
                "vote_delegated_$_to_id": {222: 1},
            }
            # test_update_vote_delegated_to_self
            # reverse("user-detail", args=[self.admin.pk]),
            # {"vote_delegated_to_id": self.admin.pk},
        )

        self.assert_status_code(response, 400)
        self.assertIn(
            "User 1 can't delegate the vote to himself.", response.json["message"]
        )

    def test_update_vote_delegated_to_invalid_id(self) -> None:
        """ User/1 tries to delegate to not existing user/42 """
        self.set_models(
            {
                "meeting/222": {"name": "Meeting222"},
                "group/1": {"meeting_id": 222, "user_ids": [1]},
                "user/1": {
                    "group_$_ids": ["222"],
                    "group_$222_ids": [1],
                },
            },
        )
        response = self.request(
            "user.update",
            {
                "id": 1,
                "vote_delegated_$_to_id": {222: 42},
            }
            # test_update_vote_delegation_invalid_id
            # reverse("user-detail", args=[self.admin.pk]),
            # {"vote_delegated_to_id": 42},
        )

        self.assert_status_code(response, 400)
        self.assertIn(
            "Datastore service sends HTTP 400. Model 'user/42' does not exist.",
            response.json["message"],
        )

    def test_update_vote_delegations_from_self(self) -> None:
        """ user/1 tries to delegate to himself """
        self.set_models(
            {
                "meeting/222": {"name": "Meeting222"},
                "group/1": {"meeting_id": 222, "user_ids": [1]},
                "user/1": {
                    "group_$_ids": ["222"],
                    "group_$222_ids": [1],
                },
            },
        )
        response = self.request(
            "user.update",
            {
                "id": 1,
                "vote_delegations_$_from_ids": {222: [1]},
            }
            # test_update_vote_delegated_from_self
            # reverse("user-detail", args=[self.admin.pk]),
            # {"vote_delegated_from_users_id": [self.admin.pk]},
        )

        self.assert_status_code(response, 400)
        self.assertIn(
            "User 1 can't delegate the vote to himself.", response.json["message"]
        )

    def test_update_vote_delegations_from_invalid_id(self) -> None:
        """ user/1 receives delegation from non existing user/1234 """
        self.set_models(
            {
                "meeting/222": {"name": "Meeting222"},
                "group/1": {"meeting_id": 222, "user_ids": [1]},
                "user/1": {
                    "group_$_ids": ["222"],
                    "group_$222_ids": [1],
                },
            },
        )
        response = self.request(
            "user.update",
            {
                "id": 1,
                "vote_delegations_$_from_ids": {222: [1234]},
            }
            # test_update_vote_delegated_from_invalid_id(
            # reverse("user-detail", args=[self.admin.pk]),
            # {"vote_delegated_from_users_id": [1234]},
        )

        self.assert_status_code(response, 400)
        self.assertIn(
            "Datastore service sends HTTP 400. Model 'user/1234' does not exist.",
            response.json["message"],
        )

    def test_update_reset_vote_delegated_to(self) -> None:
        """ user/3->user/2: user/3 wants to reset delegation to user/2"""
        self.setup_vote_delegation()
        response = self.request(
            "user.update",
            {
                "id": 3,
                "vote_delegated_$_to_id": {222: None},
            }
            # test_update_reset_vote_delegated_to
            # reverse("user-detail", args=[self.user.pk]),
            # {"vote_delegated_to_id": None},
        )

        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "vote_delegations_$222_from_ids": [4],
                "vote_delegations_$_from_ids": ["222"],
            },
        )
        self.assert_model_exists(
            "user/3",
            {
                "vote_delegated_$222_to_id": None,
                "vote_delegated_$_to_id": [],
            },
        )

    def test_update_reset_vote_delegations_from(self) -> None:
        """ user/3/4->user/2: user/2 wants to reset delegation from user/3"""
        self.setup_vote_delegation()
        response = self.request(
            "user.update",
            {
                "id": 2,
                "vote_delegations_$_from_ids": {222: [4]},
            }
            # test_update_reset_vote_delegated_from
            # reverse("user-detail", args=[self.user2.pk]),
            # {"vote_delegated_from_users_id": []},
        )

        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "vote_delegations_$222_from_ids": [4],
                "vote_delegations_$_from_ids": ["222"],
            },
        )
        self.assert_model_exists(
            "user/3",
            {
                "vote_delegated_$222_to_id": None,
                "vote_delegated_$_to_id": [],
            },
        )

    def test_update_no_reset_vote_delegations_from_on_none(self) -> None:
        """ user/3/4->user/2: user/2 wants to reset all delegations"""
        self.setup_vote_delegation()
        response = self.request(
            "user.update",
            {
                "id": 2,
                "vote_delegations_$_from_ids": {222: []},
            }
            # test_update_no_reset_vote_delegated_from_on_none
            # reverse("user-detail", args=[self.user2.pk]),
            # {"vote_delegated_from_users_id": None},
        )

        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "vote_delegations_$222_from_ids": [],
                "vote_delegations_$_from_ids": ["222"],
            },
        )
        self.assert_model_exists(
            "user/3",
            {
                "vote_delegated_$222_to_id": None,
                "vote_delegated_$_to_id": [],
            },
        )

    def test_update_nested_vote_delegated_to_1(self) -> None:
        """ user3 -> user2: user/2 wants to delegate to user/1 """
        self.setup_vote_delegation()
        response = self.request(
            "user.update",
            {
                "id": 2,
                "vote_delegated_$_to_id": {222: 1},
            }
            # test_update_nested_vote_delegation_1
            # reverse("user-detail", args=[self.user2.pk]),
            # {"vote_delegated_to_id": self.admin.pk},
        )

        self.assert_status_code(response, 400)
        self.assertIn(
            "User 2 cannot delegate his vote, because there are votes delegated to him.",
            response.json["message"],
        )
        self.assert_model_exists(
            "user/2",
            {
                "vote_delegated_$222_to_id": None,
                "vote_delegations_$222_from_ids": [3, 4],
            },
        )

    def test_update_nested_vote_delegated_to_2(self) -> None:
        """ user3 -> user2: user/1 wants to delegate to user/3 """
        self.setup_vote_delegation()
        response = self.request(
            "user.update",
            {
                "id": 1,
                "vote_delegated_$_to_id": {222: 3},
            }
            # test_update_nested_vote_delegation_2
            # reverse("user-detail", args=[self.admin.pk]),
            # {"vote_delegated_to_id": self.user.pk},
        )

        self.assert_status_code(response, 400)
        self.assertIn(
            "User 1 cannot delegate his vote to user 3, because that user has delegated his vote himself.",
            response.json["message"],
        )

    def test_update_vote_delegated_replace_existing_to(self) -> None:
        """ user3->user/2: user/3 wants to delegate to user/1 instead to user/2 """
        self.setup_vote_delegation()
        self.assert_model_exists("user/1", {"vote_delegations_$222_from_ids": None})
        self.assert_model_exists("user/2", {"vote_delegations_$222_from_ids": [3, 4]})
        self.assert_model_exists("user/3", {"vote_delegated_$222_to_id": 2})
        self.assert_model_exists("user/4", {"vote_delegated_$222_to_id": 2})

        response = self.request(
            "user.update",
            {
                "id": 3,
                "vote_delegated_$_to_id": {222: 1},
            }
            # test_update_vote_delegation_autoupdate
            # reverse("user-detail", args=[self.user.pk]),
            # {"vote_delegated_to_id": self.admin.pk},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/1", {"vote_delegations_$222_from_ids": [3]})
        self.assert_model_exists("user/2", {"vote_delegations_$222_from_ids": [4]})
        self.assert_model_exists("user/3", {"vote_delegated_$222_to_id": 1})
        self.assert_model_exists("user/4", {"vote_delegated_$222_to_id": 2})

        # Ist 400 mit meldung: 'You can not set user/3/vote_delegated_$222_to_id to a new value because this field is not empty.'
        # Sollte die verknüpfung von user/3 zu user/1 delegieren, aber auch weg von user2

    def test_update_vote_replace_existing_delegated_to_2(self) -> None:
        # works out of the box
        """ user3->user/2: user/3 wants to delegate to user/1 instead to user/2 """
        self.setup_vote_delegation()
        self.set_models(
            {
                "user/1": {
                    "meeting_id": 222,
                    "vote_delegations_$222_from_ids": [5],
                    "vote_delegations_$_from_ids": ["222"],
                },
                "user/5": {
                    "username": "delegator5",
                    "meeting_id": 222,
                    "vote_delegated_$222_to_id": 1,
                    "vote_delegated_$_to_id": ["222"],
                },
            }
        )

        self.assert_model_exists("user/1", {"vote_delegations_$222_from_ids": [5]})
        self.assert_model_exists("user/2", {"vote_delegations_$222_from_ids": [3, 4]})
        self.assert_model_exists("user/3", {"vote_delegated_$222_to_id": 2})
        self.assert_model_exists("user/4", {"vote_delegated_$222_to_id": 2})
        self.assert_model_exists("user/5", {"vote_delegated_$222_to_id": 1})

        response = self.request(
            "user.update",
            {
                "id": 3,
                "vote_delegated_$_to_id": {222: 1},
            }
            # test_update_vote_delegation_autoupdate
            # reverse("user-detail", args=[self.user.pk]),
            # {"vote_delegated_to_id": self.admin.pk},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/1", {"vote_delegations_$222_from_ids": [5, 3]})
        self.assert_model_exists("user/2", {"vote_delegations_$222_from_ids": [4]})
        self.assert_model_exists("user/3", {"vote_delegated_$222_to_id": 1})
        self.assert_model_exists("user/4", {"vote_delegated_$222_to_id": 2})
        self.assert_model_exists("user/5", {"vote_delegated_$222_to_id": 1})

    def test_update_vote_replace_existing_delegations_from(self) -> None:
        """ user3->user/2: user/3 wants to delegate to user/1 instead to user/2 """
        self.setup_vote_delegation()
        self.set_models(
            {
                "user/1": {
                    "vote_delegations_$222_from_ids": [5],
                    "vote_delegations_$_from_ids": ["222"],
                },
                "user/5": {
                    "username": "delegator5",
                    "meeting_id": None,
                    "group_$222_ids": [1],
                    "group_$_ids": ["222"],
                    "vote_delegated_$222_to_id": 1,
                    "vote_delegated_$_to_id": ["222"],
                },
            }
        )

        response = self.request(
            "user.update",
            {
                "id": 1,
                "vote_delegations_$_from_ids": {222: [5, 3]},
            }
            # test_update_vote_delegation_autoupdate opposite
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1",
            {
                "vote_delegations_$222_from_ids": [5, 3],
                "vote_delegations_$_from_ids": ["222"],
            },
        )
        self.assert_model_exists(
            "user/2",
            {
                "vote_delegations_$222_from_ids": [4],
                "vote_delegations_$_from_ids": ["222"],
            },
        )  # ASSERT 3,4 statt 4
        self.assert_model_exists(
            "user/3",
            {"vote_delegated_$222_to_id": 1, "vote_delegated_$_to_id": ["222"]},
        )  # ASSERT None != 1
        self.assert_model_exists(
            "user/4",
            {"vote_delegated_$222_to_id": 2, "vote_delegated_$_to_id": ["222"]},
        )
        self.assert_model_exists(
            "user/5",
            {"vote_delegated_$222_to_id": 1, "vote_delegated_$_to_id": ["222"]},
        )
        # Messag: 'You can not set user/3/vote_delegated_$222_to_id to a new value because this field is not empty.'
        # from single_relation_handler.py Line 188
        # Der müsste den user/3 hier hinzufügen, bei User/3 feststellen, dass dort user/2 verknüpft ist und dann dort entfernen

    def test_update_vote_add_1_remove_other_delegations_from(self) -> None:
        """ user3/4 -> user2: delegate user/1 to user/2 and remove user/3 and 4"""
        self.setup_vote_delegation()
        response = self.request(
            "user.update",
            {
                "id": 2,
                "vote_delegations_$_from_ids": {222: [1]},
            }
            # test_update_vote_delegated_from(
            # reverse("user-detail", args=[self.user2.pk]),
            # {"vote_delegated_from_users_id": [self.admin.pk]},
        )

        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1",
            {"vote_delegated_$222_to_id": 2, "vote_delegated_$_to_id": ["222"]},
        )
        self.assert_model_exists(
            "user/2",
            {
                "vote_delegations_$222_from_ids": [1],
                "vote_delegations_$_from_ids": ["222"],
            },
        )
        self.assert_model_exists(
            "user/3",
            {"vote_delegated_$222_to_id": None, "vote_delegated_$_to_id": []},
        )

    def test_update_vote_delegations_from_nested_1(self) -> None:
        """ user3-> user2: admin tries to delegate to user/3 """
        self.setup_vote_delegation()
        response = self.request(
            "user.update",
            {
                "id": 3,
                "vote_delegations_$_from_ids": {222: [1]},
            }
            # test_update_vote_delegated_from_nested_1
            # reverse("user-detail", args=[self.user.pk]),
            # {"vote_delegated_from_users_id": [self.admin.pk]},
        )

        self.assert_status_code(response, 400)
        self.assertIn(
            "User 3 cannot receive vote delegations, because he delegated his own vote.",
            response.json["message"],
        )

    def test_update_vote_delegations_from_nested_2(self) -> None:
        """ user3 -> user2: user2 tries to delegate to admin """
        self.setup_vote_delegation()
        response = self.request(
            "user.update",
            {
                "id": 1,
                "vote_delegations_$_from_ids": {222: [2]},
            }
            # test_update_vote_delegated_from_nested_2
            # reverse("user-detail", args=[self.admin.pk]),
            # {"vote_delegated_from_users_id": [self.user2.pk]},
        )

        self.assert_status_code(response, 400)
        self.assertIn(
            "User(s) [2] can't delegate their votes , because they receive vote delegations.",
            response.json["message"],
        )

    def test_update_vote_setting_both_correct_from_to_1(self) -> None:
        """ user3/4 -> user2: user3 reset own delegation and receives other delegation """
        self.setup_vote_delegation()
        response = self.request(
            "user.update",
            {
                "id": 3,
                "vote_delegations_$_from_ids": {222: [1]},
                "vote_delegated_$_to_id": {222: None},
            }
            # completely own test
        )

        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1",
            {"vote_delegated_$222_to_id": 3, "vote_delegated_$_to_id": ["222"]},
        )
        self.assert_model_exists(
            "user/2",
            {
                "vote_delegations_$222_from_ids": [4],
                "vote_delegations_$_from_ids": ["222"],
            },
        )
        self.assert_model_exists(
            "user/3",
            {
                "vote_delegated_$_to_id": [],
                "vote_delegations_$222_from_ids": [1],
                "vote_delegations_$_from_ids": ["222"],
            },
        )
        self.assert_model_exists(
            "user/4",
            {"vote_delegated_$222_to_id": 2, "vote_delegated_$_to_id": ["222"]},
        )

    def test_update_vote_setting_both_correct_from_to_2(self) -> None:
        """ user3/4 -> user2: user2 delegates to user/1 and resets it's received delegations """
        self.setup_vote_delegation()
        response = self.request(
            "user.update",
            {
                "id": 2,
                "vote_delegations_$_from_ids": {222: []},
                "vote_delegated_$_to_id": {222: 1},
            }
            # completely own test
        )

        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "vote_delegated_$222_to_id": 1,
                "vote_delegated_$_to_id": ["222"],
                "vote_delegations_$222_from_ids": [],
                "vote_delegations_$_from_ids": ["222"],
            },
        )
        self.assert_model_exists(
            "user/1",
            {
                "vote_delegated_$_to_id": None,
                "vote_delegations_$222_from_ids": [2],
                "vote_delegations_$_from_ids": ["222"],
            },
        )
        self.assert_model_exists("user/3", {"vote_delegated_$_to_id": []})
        self.assert_model_exists("user/4", {"vote_delegated_$_to_id": []})

    def test_update_vote_setting_both_from_to_error(self) -> None:
        """ user3/4 -> user2: user2 delegates to user/3 and resets received delegation from user/3 """
        self.setup_vote_delegation()
        response = self.request(
            "user.update",
            {
                "id": 2,
                "vote_delegations_$_from_ids": {222: [4]},
                "vote_delegated_$_to_id": {222: 3},
            }
            # completely own test
        )

        self.assert_status_code(response, 400)
        self.assertIn('User 2 cannot delegate his vote, because there are votes delegated to him.', response.json["message"])

    def test_update_vote_add_remove_delegations_from(self) -> None:
        """ user3/4 -> user2: user2 removes 4 and adds 1 delegations_from """
        self.setup_vote_delegation()
        response = self.request(
            "user.update",
            {
                "id": 2,
                "vote_delegations_$_from_ids": {222: [3, 1]},
            },
        )

        self.assert_status_code(response, 200)
        self.assert_model_exists("user/1", {"vote_delegated_$222_to_id": 2})
        user2 = self.get_model("user/2")
        self.assertCountEqual(user2["vote_delegations_$222_from_ids"], [1, 3])
        self.assert_model_exists("user/3", {"vote_delegated_$222_to_id": 2})
        user4 = self.get_model("user/4")
        self.assertIn(user4.get("vote_delegated_$222_to_id"), (None, []))

    def test_update_delegated_to_own_meeting(self) -> None:
        """ user/1 delegates to user/2 """
        self.set_models(
            {
                "meeting/222": {"name": "Meeting222"},
                "group/1": {"meeting_id": 222, "user_ids": [1]},
                "meeting/223": {"name": "Meeting223"},
                "group/2": {"meeting_id": 223, "user_ids": [2]},
                "user/1": {
                    "group_$_ids": ["222"],
                    "group_$222_ids": [1],
                },
                "user/2": {
                    "group_$_ids": ["223"],
                    "group_$223_ids": [2],
                },
            }
        )

        response = self.request(
            "user.update",
            {
                "id": 1,
                "vote_delegated_$_to_id": {222: 2},
            },
        )

        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 222: [FullQualifiedId('user/2')]",
            response.json["message"],
        )

    def test_update_delegated_to_other_meeting(self) -> None:
        """ user/1 delegates to user/2 """
        self.set_models(
            {
                "meeting/222": {"name": "Meeting222"},
                "group/1": {"meeting_id": 222, "user_ids": [1]},
                "meeting/223": {"name": "Meeting223"},
                "group/2": {"meeting_id": 223, "user_ids": [2]},
                "user/1": {
                    "group_$_ids": ["222"],
                    "group_$222_ids": [1],
                },
                "user/2": {
                    "group_$_ids": ["223"],
                    "group_$223_ids": [2],
                },
            }
        )
        response = self.request(
            "user.update",
            {
                "id": 1,
                "vote_delegated_$_to_id": {223: 2},
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 223: [FullQualifiedId('user/1')]",
            response.json["message"],
        )

    def test_update_delegation_from_own_meeting(self) -> None:
        """ user/1 receive vote from user/2 """
        self.set_models(
            {
                "meeting/222": {"name": "Meeting222"},
                "group/1": {"meeting_id": 222, "user_ids": [1]},
                "meeting/223": {"name": "Meeting223"},
                "group/2": {"meeting_id": 223, "user_ids": [2]},
                "user/1": {
                    "group_$_ids": ["222"],
                    "group_$222_ids": [1],
                },
                "user/2": {
                    "group_$_ids": ["223"],
                    "group_$223_ids": [2],
                },
            }
        )
        response = self.request(
            "user.update",
            {
                "id": 1,
                "vote_delegations_$_from_ids": {222: [2]},
            },
        )

        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 222: [FullQualifiedId('user/2')]",
            response.json["message"],
        )

    def test_update_delegation_from_other_meeting(self) -> None:
        """ user/1 receive vote from user/2 """
        self.set_models(
            {
                "meeting/222": {"name": "Meeting222"},
                "group/1": {"meeting_id": 222, "user_ids": [1]},
                "meeting/223": {"name": "Meeting223"},
                "group/2": {"meeting_id": 223, "user_ids": [2]},
                "user/1": {
                    "group_$_ids": ["222"],
                    "group_$222_ids": [1],
                },
                "user/2": {
                    "group_$_ids": ["223"],
                    "group_$223_ids": [2],
                },
            }
        )

        response = self.request(
            "user.update",
            {
                "id": 1,
                "vote_delegations_$_from_ids": {223: [2]},
            },
        )

        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 223: [FullQualifiedId('user/1')]",
            response.json["message"],
        )
