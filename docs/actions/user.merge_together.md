**THIS IS A DRAFT AND NOT CURRENTLY IMPLEMENTED.**

## Payload
```
{
// Required
    user_ids: Id[];
    username: string;

// Optional
    title: string;
    first_name: string;
    last_name: string;
    is_active: boolean;
    is_physical_person: boolean;
    default_password: string;
    gender: string;
    email: string;
    default_structure_level: string;
    default_vote_weight: decimal(6);

    password_from_user_id: number;
}
```

## Action
The action is some kind of [user.create](user.create): It creates a user and puts him in the place of all given
users (= users in `user_ids`) and finally, all given users are deleted.

TODO: If actually implemented, this needs to be updated to remove the template fields.

Create a new user with the information given in the request. Handling of other fields:
- `number_$`: Merge.
- `structure_level_$`: Merge.
- `vote_weight_$`: Merge.
- `about_me_$`: Merge.
- `comment_$`: Merge.
- `committee_ids`: The union of committees from all meetings of the old temporary users.
- `is_present_in_meeting_ids`: Merge.
- `organization_management_level`: Set to `null`.

All other relations are merged:
- `group_$_ids`
- `speaker_$_ids`
- `personal_note_$_ids`
- `supported_motion_$_ids`
- `submitted_motion_$_ids`
- `poll_voted_$_ids`
- `option_$_ids`
- `vote_$_ids`
- `vote_delegated_vote_$_ids`
- `assignment_candidate_$_ids`
- `vote_delegated_$_to_id`
- `vote_delegations_$_from_ids`

Note that the `username` can be one of the given users usernames or a new one - the uniqueness must be checked within all other users.

If `password_from_user_id` is given, the password hash from this user is copied. The user id must be given in `user_ids`! If it is empty, the default password is used. 

Important:

All reverse relations to the given temporary users must be changed to the new id of the created user.

Finally, delete all given users.

## Permissions
The request user needs the organization management level `can_manage_users`.

## Client

The client could/should fill the optional fields from a chosen "main" user to not force the editor to rewrite all the data.