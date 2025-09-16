## Payload
```js
{
// Required
    meeting_ids: Ids;
    agenda_item_ids: Ids;

// Optional
    with_speakers: boolean;
    with_moderator_notes: boolean;
    with_attachments: boolean;
}
```

## Action
Forwards the agenda items given via the `agenda_item_ids` to the meetings given by the `meeting_ids`.

The agenda items all need to be part of the same meeting.
The meetings all need to be included in committees that can receive agenda forwardings from the origin meetings committee. This is defined via membership in the relation `receive_agenda_forwardings_from_committee_ids`.

This only works with agenda items linking to topics.
Should the `agenda_item_ids` contain any agenda items linking to motions or assignments, an exception is thrown.

Upon forwarding for every topic and every target meeting:
- A new topic is created in the target meeting with the same title and text as the original linked topic.
- The agenda item linked to said topic is given the same `type` as the original agenda_item.

If `with_speakers` is true:
- An exception is thrown if there is any paused or started speakers, or any waiting points of order, connected to any of the topics list of speakers.
- Otherwise all speakers are copied over.
   - Restrictions concerning presence in the target meeting are ignored.
   - Restrictions concerning having multiple speakers with the same user in the target meeting are ignored.
   - If a user behind a speaker isn't part of the target meeting, he will be added to it. Groups and structure levels in this case will be matched via name. Should a group or structure level by that name not exist in the target meeting yet, it will be created.
   - Structure levels for the speakers (not the users) are matched by name. If one doesn't exist yet, it will be created.
   - The groups of all users, that were present in the target meeting already, will be updated in the target meetings to include the groups from the original meeting (again, matched by name, potentially created if not found). The same does _not_ happen for structure levels or any other meeting_user data.
   - Newly created groups will have no permissions.
- `structure_level_list_of_speakers` are copied over if they exist.
If `with_moderator_notes` is true:
- For any new topic, the newly generated list of speakers receive the origin topics list of speakers `moderator_notes` value.
If `with_attachments` is true:
- All files connected to any of the topics are copied into the target meeting and the copies are connected with the created topics.

## Permissions
The request user needs `agenda_item.can_forward` in the source meeting. There are no rights needed in the receiving meeting, unless `with_speakers` is said, in which case `user.can_manage` is required in all target meetings.
