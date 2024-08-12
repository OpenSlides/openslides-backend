## Payload

```js
{
    user_ids: Id[];
}
```

## Returns

```js
{
  [user_id: Id]: {
    organization_management_level: OML-String,
    committees: [{ id: Id; name: String; cml: CML-String; }],
    meetings: [{
      id: Id;
      name: String;
      is_active_in_organization_id: Id;
      is_locked: boolean;
      motion_submitter_ids: Id[];
      assignment_candidate_ids: Id[];
      speaker_ids: Id[];
      locked_out: boolean;
    }]
  }
}
```

## Logic

It iterates over the given `user_ids`. For every id of `user_ids` all objects are searched which are associated with that id. This means that for every committee it is checked if the user (specified by the id) is a manager or member of the committee, and for every meeting if the user is listed as a speaker of any `agenda_item` or as a submitter of any `motion` or as a candidate of any `assignment`.
The result is a dictionary whose keys are the `user_ids`. The values are threefolded: `organization_management_level` contains the OML of the user. The two other values are arrays, one for the `committees` and one for the `meetings`. If a user is no member of any committee, then the `committees` array is empty and omitted. The same applies to the `meetings` array.
If a meeting has `locked_from_inside` set to true, `is_locked` will be true and `motion_submitter_ids`, `assignment_candidate_ids` and `speaker_ids`, `locked_out` will be left out for this meeting, unless the calling user is in the meeting himself.

To make the distinction clear: `is_locked` denominates that the entire meeting has been locked from inside, `locked_out` means that only the user has been locked out of the meeting.

Every committee is given by its name and id as well as the CML of the user (given by the `user_id`). Every meeting is given by its name, its id and its `is_active_in_organization_id` (to indicate if the meeting is archived).

## Permissions

The common usage of this presenter is the preview on deletion of users. Therefore the permissions are identical to that of the action [user.delete](../actions/user.delete.md):

See [Permissions for altering a user](https://github.com/OpenSlides/OpenSlides/wiki/Users#Permissions-for-altering-a-user). Additionally the OML-Level of the request user must be higher or equal than the requested user's one.
