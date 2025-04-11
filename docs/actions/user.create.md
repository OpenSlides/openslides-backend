## Payload
```js
{
// Optional
// Group A
    title: string;
    username: string;
    pronoun: string;
    first_name: string;
    last_name: string;
    is_active: boolean;
    is_physical_person: boolean;
    can_change_own_password: boolean;
    gender_id: Id;
    email: string;
    member_number: string;
    default_vote_weight: decimal(6);
    guest: boolean;

// Group B
    number: string;
    vote_weight: decimal;
    about_me: HTML;
    comment: HTML;
    locked_out: boolean;

    structure_level_id: Id;
    vote_delegated_to_id: Id;
    vote_delegations_from_ids: Id[];
    is_present_in_meeting_ids: Id[];

// Group C
    meeting_id: Id; // required if there are group B or C fields. All Group B and C fields are part of this meeting.
                    // meeting_id belongs to group C, because this group is less restrictive.
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
    saml_id: boolean;

// Group I
    home_committee_id: Id;

// Group J
    guest: boolean;

// Only internal
    forwarding_committee_ids
}
```

## Action
Creates a user. 
* The field `organization_management_level` can only be set as high as the request users `organization_management_level` and defaults to `null`.
* If no `default_password` is given a random one is generated. The default password is hashed via the auth service and the hash is saved within `password`. A given `default_password`is also stored as hashed password.
* If `username` is given, it has to be unique within all users. If there already exists a user with the same username, an error is returned. If the `username` is not given, 1. the saml_id is used or 2. it has to be generated (see [user.create#generate-a-username](user.create.md#generate-a-username) below). Also the username may not contain spaces.
* The `organization_management_level` as restring can be taken from the enum of this user field.
* Remove starting and trailing spaces from `username`, `first_name` and `last_name`.
* The given `gender_id` must be present in the database.
* If `saml_id` is set in payload, there may be no `password` or `default_password` set or generated and `set_change_own_password` will be set to False.
* The `member_number` must be unique within all users.
* Throws an error if the `group_ids` contain the meetings `anonymous_group_id`.
* Checks, whether at the end the field `locked_out` will be set together with any of `user.can_manage` or any admin statuses on the created user and throws an error if that is the case.
* `guest` can't be true if `home_committee_id` is set.

### Generate a username
If no username is given, it is set from a given `saml_id`. Otherwise it is generated from `first_name` and `last_name`. Joins all non-empty values from these two fields in the given order. If both fields are empty, raise an error, that one of the fields is required (see [OS3](https://github.com/OpenSlides/OpenSlides/blob/main/server/openslides/users/serializers.py#L90)). Remove all spaces from a generated username.

Check, if the generated username is unique. If not do the following in a loop:

Append a number starting at 1 to the username (append with a space). Check if the username is unique. If not increase the number. Do this until a free username is found.

### Return value

```js
{
    id: Id;
    meeting_user_id: Id; // Optional, only if `meeting_id` was present in the payload
}
```

## Permissions
The request user needs the basic permissions, see [Permissions for altering a user](https://github.com/OpenSlides/OpenSlides/wiki/Users#Permissions-for-altering-a-user).

Group A:

No special permissions

Group B:

The request user needs `user.can_manage` in the meeting of meeting_id.

Group C:

For each meeting the request user must satisfy at least one of:
- `user.can_manage` for the meeting, OR
- If the meeting is not locked via `locked_from_inside` setting:
  * the OML `can_manage_users` in the organization
  * The CML `can_manage` for the committee of the meeting

Group D:

The request user must satisfy at least one of:
- the OML `can_manage_users`
- the CML `can_manage` for each referenced committee

Group E:

The request user needs the OML equal or higher than that he wants to set. So the minimum is `can_manage_users`.

Group F:

The request user needs the permissions under the rules of user_scope, see [Permissions for altering a user](https://github.com/OpenSlides/OpenSlides/wiki/Users#Permissions-for-altering-a-user), but at minimum the OML-Level of the requested user.

Group G:

The request user needs the OML superadmin.

Group H:

Group H fields are only allowed in internal requests or, exclusive for user.create, with OML permission `can_manage_users`

Group I:

CML `can_manage` for the new `home_committee_id` if there is one and CML `can_manage` for the old `home_committee_id` if there is one.

Group J:

Group I permissions and if there is no home committee (old or new) Group A Permissions