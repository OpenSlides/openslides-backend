## Payload
```
{
// Required
    meeting_id: Id;
    title: string;
    text: HTML;
    origin_id: Id;

// Optional
    reason: HTML;
}
```

## Action
Creates a new motion. This action is very similar to [motion.create](motion.create.md) but very restricted in it's inputs.

`origin_id` is an id of another motion (potentially not from this meeting!) referred to as the _origin motion_. The given motion is forwarded from the meeting of the _origin motion_ (A) to the given meeting (by `meeting_id` in the payload) (B). It must be checked, that `B/committee_id` is included in `A/committee_id -> committee/forward_to_committee_ids`.

The motion is created with all special rules for [motion.create](motion.create.md): The state/workflow and
timestamps must be set, a list of speakers must be created, and so on. There is one little catch: If
the given meeting has `meeting/motions_reason_required` set, it is ok for `reason` to be empty.

The original motion must be updated as well (this is done by the automatic relation handling):
* The unique `id` of the newly created motion has to be linked to the _origin motion_s `derived_motion_ids` field.
  * Deleting the newly created motion has to ensure that the corresponding entry was removed from the _origin motion_s `derived_motion_ids` field

### Forwarding tree fields

* `all_origin_ids` of the newly created motion must be set to `all_origin_ids` of the origin motion plus the given `origin_id`. It is important that the id is appended at the end of the list, since the order of this field represents the order of the tree in case a motion of the tree is deleted.
* The id of the newly created motion must be added to the `all_derived_motion_ids` field of all motions in the `all_origin_ids` field of this motion. Order is not important here.

### New user in receiving meeting

* A new user on committee level will be generated automatically _inactive_ with meeting standard group and committee's name. This user is stored in the committee as `forwarding_user` and used in further forwardings, if necessary with new membership in standard group of new meetings.

### State needs to allow forwarding

* The origin state must allow forwarding (`allow_motion_forwarding` must be set to True).

## Permissions
The request user needs `motion.can_forward` in the source meeting. `motion.can_manage` is not explicitly needed for the request user, because it is included. There are no rights needed in the receiving meeting.

### Exceptions

Although they would have meaningful title, text and reason, amendment motions (motions with a field `lead_motion_id`), should not be forwarded directly. The backend should throw an error if an amendment was requested to be forwarded.
The client does not offer to forward an amendment.
