### Includes changes of feature branch `los-extension`!

## Payload
```
{
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
}
```

## Action
Creates a user. 
* The field `organization_management_level` can only be set as high as the request users `organization_management_level` and defaults to `null`.
* If no `default_password` is given a random one is generated. The default password is hashed via the auth service and the hash is saved within `password`. A given `default_password`is also stored as hashed password.
* If `username` is given, it has to be unique within all users. If there already exists a user with the same username, an error must be returned. If the `username` is not given, 1. the saml_id will be used or 2. it has to be generated (see [[user.create#generate-a-username]] below). Also the username may not contain spaces.
* The `organization_management_level` as restring can be taken from the enum of this user field.
* Remove starting and trailing spaces from `username`, `first_name` and `last_name`
* The given `gender` must be present in `organization/genders`
* If `saml_id` is set in payload, there may be no `password` or `default_password` set or generated and `set_change_own_password` will be set to False.

### Generate a username
If no username is given, it will be set from a given `saml_id`. Otherwise it is generated from `first_name` and `last_name`. Join all non-empty values from these two fields in the given order. If both fields are empty, raise an error, that one of the fields is required (see [OS3](https://github.com/OpenSlides/OpenSlides/blob/main/server/openslides/users/serializers.py#L90)). Remove all spaces from a generated username.

Check, if the generated username is unique. If not do the following in a loop:

Append a number starting at 1 to the username (append with a space). Check if the username is unique. If not increase the number. Do this until a free username is found.

### Return value

```
{
    id: Id;
    meeting_user_id?: Id; // only if `meeting_id` was present in the payload
}
```

## Permissions
The request user needs the basic permissions, see [[users#Permissions-for-altering-a-user]].

Group A:

No special permissions

Group B:

The request user needs `user.can_manage` in the meeting of meeting_id.

Group C:

The request user must satisfy at least one of:
- the OML `can_manage_users`
- For each meeting:
  * `user.can_manage` for the meeting, OR
  * The CML `can_manage` for the committee of the meeting

Group D:

The request user must satisfy at least one of:
- the OML `can_manage_users`
- the CML `can_manage` for each referenced committee

Group E:

The request user needs the OML equal or higher than that he wants to set. So the minimum is `can_manage_users`.

Group F:

The request user needs the permissions under the rules of user_scope, see [[users#Permissions-for-altering-a-user]], but at minimum the OML-Level of the requested user.

Group G:

The request user needs the OML superadmin.

Group H:

Group H fields are only allowed in internal requests or, exclusive for user.create, with OML permission `can_manage_users`
