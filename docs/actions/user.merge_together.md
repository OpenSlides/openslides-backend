## Payload
```
{
// Required
    id: Id // The user the others will be merged into
    user_ids: Id[];

// Optional
    username: string;
    title: string;
    first_name: string;
    last_name: string;
    is_active: boolean;
    is_physical_person: boolean;
    default_password: string;
    gender: string;
    email: string;
    default_vote_weight: decimal(6);
}
```
    #TODO: Fill in some other account-side user.update fields?

## Action
The action is some kind of [user.update](user.update.md): It updates the primary user fields (if they are empty) with the user-model values of the other users in the order that their ids appear in the user_ids list, merges the `meeting_users` the same way, overwrites certain account fields if given and deletes the non-primary users.
Conflicts in single-relations should be resolved on a case-by-case basis<!-- TODO: What should be done with the specific single relations?-->

Create a new user with the information given in the request. Handling of other fields:
- `committee_ids`: The union of committees from all meetings of the old temporary users.
- `organization_management_level`: Set to highest oml among the users.
<!--TODO: Fill in some other account-side user.update fields?-->

As for related meeting_users, they should be merged. 
If there are conflicts in meetings because two or more of the users are present in the same one:
- All `ids`-relations should be unified
- For `id`-relations and other fields should be generically treated like the fields in the related `user` model

Note that the `username` can be one of the given users usernames or a new one - the uniqueness must be checked within all other users.

Important:

All reverse relations to the given users must be changed to the new id of the created user.

Finally, delete all given extra users.

## Permissions
The request user needs the organization management level `can_manage_users`.

## Client

The client could/should fill the optional fields from a chosen "main" user to not force the editor to rewrite all the data.