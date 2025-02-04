## Payload
```
{
// Required
    id: Id // The primary user the others will be merged into
    user_ids: Id[];

// Optional
    username: string;
    title: string;
    first_name: string;
    last_name: string;
    is_active: boolean;
    is_physical_person: boolean;
    default_password: string;
    gender_id: Id;
    email: string;
    default_vote_weight: decimal(6);
    pronoun: string;
    member_number: string;
}
```

## Definitions
- `primary user` or `main user`: The user defined by the `id`
- `secondary users` or `other users`: The users defined in the `user_ids` field
- `selected users`: Both the `primary` and `secondary users`
- User ranking: Primary user is ranked above all secondary users, the secondary users are ranked according to their ids position in the `user_ids` field

## Action
The action is a kind of expanded [user.update](user.update.md): It updates the primary user fields with the user-model values of the secondary users in the order that their ids appear in the user_ids list, merges the `meeting_users` and related models the same way, overwrites the account fields in the payload with the given values if there are any and deletes the merged models.

Conflicts in single-relations are resolved on a case-by-case basis.

This action will overwrite data in archived meetings.
It will also cause old-format `vote_weight` values (i.e. entries with the value `0.000000`) to be replaced by the value `0.000001`, which is legal in the current system.

### Restrictions
An error is thrown if:
- The operator is trying to merge himself into another user
- Any of the selected users are demo- or forwarding users (i.e. `is_demo_user` or `forwarding_committee_ids` is set)
- Any of the secondary users have a `saml_id`
- There are multiple different `member_number`s between the selected users (empty does not count)
- There are conflicts regarding polls, i.e. two or more of the selected users...
    - are option content_objects (not counting poll_candidate_list membership) on the same poll
    - are candidates on the same poll_candidate_list
    - have voted on the same poll (delegated or not)
    - Any affected meeting_users have groups that are currently entitled to work on any poll
- Any affected meeting_users _who share a meeting_:
    - have running speakers
    - are in a meeting without `list_of_speakers_allow_multiple_speakers` and have waiting speakers on the same list who cannot be merged together into at most one point_of_order and one normal speech. Speeches may not be merged if there are multiple different values (empty does count) within any of the fields:
        - `speech_state`
        - `point_of_order_category_id`
        - `note`
        - `structure_level_list_of_speakers_id`

### Functionality
The primary user is updated with the information from the secondary users using the following rules:
- `organization_management_level` is set to highest oml among the users.
- `can_change_own_password` is set to true if it is true on any selected user, unless the primary user has a `saml_id`, in which case it is ignored.
- relation-lists are set to the union of their content among all selected users, except the `is_present_in_meeting_ids`- and `meeting_user_ids`-relation, which are handled separately
- login data (`saml_id`, `username`, `password`) remains untouched
- If any user has a`member_number` it is used
- The `is_present_in_meeting_ids` relation list will be expanded with all meetings
- `meeting_user_ids` are create-merged (see "Merging of sub-collections/Create merge" and "Meeting user merge")
- All other fields are left as-is

Any date in the custom payload data from the request overwrites anything that would otherwise be determined for that field by the above rules.

Data validity of the results is checked according to user.update rules.

The secondary users are deleted.

Any poll that contains the id of any secondary user in its `entitled_users_at_stop` list will have it re-written to _additionally_ contain the new user id.
This means that a line
`{"voted": false, "present": true, "user_id": 4, "vote_delegated_to_user_id": 7}`
becomes
`{"voted": false, "present": true, "user_id": 4, "vote_delegated_to_user_id": 7, "user_merged_into_id": 2, "delegation_user_merged_into_id": 10}`
after two merges where for the first `user/4` was merged into `user/2` and for the second `user/7` was merged into `user/10`.
This is to ensure that the client can recognize where users were merged, as simply replacing the ids may cause situations where a user is present on a list twice and not replacing them would mean that the user that voted would not be recognizable anymore.

#### Merging of sub-collections
Relation lists where simple unification does not suffice (usually because the target collections function mostly as a type of m:n connection between two other collections) are merged. 

For that purpose, target models for these relations are compared and those that are judged to fulfill equivalent roles are grouped together.

Criteria for equivalence depend on the collection in question.

Within every group, models are ranked in accordance to the rank of their parent models and then merged in accordance with the field appropriate merge type: update-merge or create-merge

##### Update merge
Each merge group is considered separately:
The first model in the group is the primary model, all others are secondary models.

Models in each merge group (if there are secondary models) are generally merged in a manner similar to how the user is merged, with individual rules determined for each collection.

The secondary models are deleted.

All remaining models are (re-)connected to the parent primary model whose merge called this one.

##### Create merge
Like normal merge until the last step:
If a remaining model is not yet connected to the primary model of the parent merge, instead of updating, it is deleted and a new model with the same data is created.

This is usually necessary in cases where the relation is set to cascade-delete

#### Meeting user merge
Equivalence is determined via `meeting_id`: All meeting_users with the same `meeting_id` are grouped together.

The primary model is updated/re-created with the information from the secondary models using the following rules:
- `assignment_candidate_ids` are update-merged
- `motion_editor_ids`, `motion_submitter_ids`, `motion_working_group_speaker_ids`, `personal_note_ids` and `speaker_ids` are create-merged
- other relation-lists are set to the union of their content among all selected users
- `comment`, `number`, `about_me`, `vote_weight`, `vote_delegated_to_id` are set to the value from the highest ranked model that has the field
- `locked_out` is set to whatever the primary model of the sub-merge has

#### Personal note merge
Equivalence is determined via equivalence of `content_object_id`

The primary model is updated/re-created with the information from the secondary models using the following rules:
- `star` is set to true if it is true on any selected model.
- `note` is set to the value from the highest ranked model that has the field

#### Motion working group speaker, motion editor, motion submitter, speaker and assignment candidate merges
Equivalence is determined as follows for each collection:
- For the `speaker` collection:
    - `list_of_speakers_allow_multiple_speakers` must be enabled in the meeting, else they are never equivalent
    - the `list_of_speakers_id` must be the same
    - they must be waiting (i.e. `begin_time` and `end_time` are None), else they are never equivalent
    - `point_of_order` truthy value must be the same
- `assignment_candidate`: Equivalence of `assignment_id`
- others: Equivalence of `motion_id`

The primary model is updated/re-created with the lowest `weight` among the selected models.

## Permissions
The request user needs at least the organization management level `can_manage_users`.
He also needs a organization management level that is equal or higher than that of all of the selected users.

## Client

The client could/should fill the optional fields from a chosen "main" user to not force the editor to rewrite all the data.

Warnings should be shown alerting the user that 
- this action is not reversable,
- will potentially change/overwrite data in archived meetings and
- will neither port the history information of the secondary users to the new ones nor rewrite the user id in the "Changed by" column