## Payload
```
{
// Required
    id: Id;

// Optional
// Group A
    title: string;
    first_name: string;
    last_name: string;
    username: string;
    is_active: boolean;
    is_physical_person: boolean;
    can_change_own_password: boolean;
    gender: string;
    pronoun: string;
    email: string;
    default_vote_weight: decimal(6);

// Group B
    number: string;
    vote_weight: decimal;
    about_me: HTML;
    comment: HTML;

    structure_level_id: Id;
    vote_delegated_to_id: Id;
    vote_delegations_from_ids: Id[];

// Group C
    meeting_id: Id;  # required if there are group B or C fields. All Group B and C fields are part of this meeting.
                     # meeting_id belongs to group C, because this group is less restrictive.
    group_ids: Id[];

// Group D
    committee_management_ids: Id[];

// Group E
    organization_management_level: string;

// Group F
   default_password: string;

// Group G
    is_demo_user: boolean;

// Group H
    saml_id: string;
}
```

## Action
Updates a user.
* The field `organization_management_level` can only be set as high as the request users `organization_management_level`. A user cannot withdraw/change his own OML "superadmin" or set himself inactive.
* The `username` must be unique within all users. It may not contain spaces.
* The `organization_management_level` as replacement can be taken from the enum of the field user.organization_management_level.
* Remove starting and trailing spaces from `username`, `first_name` and `last_name`
* The given `gender` must be present in `organization/genders`

Note: `is_present_in_meeting_ids` is not available in update, since there is no possibility to partially update this field. This can be done via [user.set_present](user.set_present.md).

If the user is removed from all groups of the meeting, all his unstarted speakers in that meeting will be deleted.

## Permissions
If the OML of the request user is lower than the OML of the user to update, only meeting-specific fields (groups B and C) are allowed to be changed. If any other fields are present in the payload, the request must fail.
If the user to be updated has a `saml_id`, the fields `can_change_own_password` and
`default_password` may not be set, because the user is a SingleSignOn user. If the saml_id will be set, the fields `default_password` and `password` will be set empty and `can_change_own_password` will be set to `False`.

Group A:

See [Permissions for altering a user](https://github.com/OpenSlides/OpenSlides/wiki/Users#Permissions-for-altering-a-user).

Group B:

The request user needs `user.can_update` in each referenced meeting.

Group C:

The request user must satisfy at least one of:
- the OML `can_manage_users`
- `user.can_update` for the meeting, OR
- The CML `can_manage` for the committee of the meeting

Group D:

The request user must satisfy at least one of:
- the OML `can_manage_users`
- the CML `can_manage` for each referenced committee

Group E:

The request user needs the OML equal or higher than that he wants to set. So the minimum is `can_manage_users`.

Group F:

The request user needs the permissions under the rules of user_scope, see [Permissions for altering a user](https://github.com/OpenSlides/OpenSlides/wiki/Users#Permissions-for-altering-a-user), but at minimum the OML of the requested user.

Group G:

The request user needs the OML `superadmin`.

Group H:

Group H fields are only allowed in internal requests