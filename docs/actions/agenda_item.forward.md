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
- The agenda item linked to said topic is given the same `type` and `comment`.
- The new agenda items `weight` will be the original items `weight` plus the maximum weight in the new meeting.
- Agenda item parentage is preserved as best as possible concerning the agenda_items that are actually sent over. This means that if a connectory item between two items is removed, the copy of the grandchild would be set as the child of the copy of the grandparent, and so on.

If `with_speakers` is true:
- The new list of speakers is closed if the original was closed as well.
- An exception is thrown if there is any paused or started speakers, or any waiting points of order, connected to any of the topics list of speakers.
- Otherwise all speakers are copied over.
   - Restrictions concerning presence in the target meeting are ignored.
   - Restrictions concerning having multiple speakers with the same user in the target meeting are ignored.
   - If a user behind a speaker isn't part of the target meeting, he will be added to it. Structure levels in this case will be matched via name. Should a structure level by that name not exist in the target meeting yet, it will be created.
   - Other meeting user fields to be transferred are `comment`, `number` and `about_me`, but only for new meeting_users.
   - The groups of all users will be updated in the target meetings to include all groups they had in the origin meeting (again, potentially created if not found).
   - Newly created groups will have no permissions.
   - Point of order categories are matched by text and, if not present, copied over, with rank being left as-is
- `structure_level_list_of_speakers` are copied over if they exist, retaining the countdown, with structure_level being matched by name and potentially created.
If `with_moderator_notes` is true:
- For any new topic, the newly generated list of speakers receive the origin topics list of speakers `moderator_notes` value.
If `with_attachments` is true:
- All files connected to any of the topics are copied into the target meeting and the copies are connected with the created topics.
- If any of the attached files is a directory, the children are also copied over.
- Access groups are always the new meetings admin group.
- `create_timestamp` should be the creation of the copy.
- Published orga files will be used as-is.

## Permissions
The request user needs to have admin rights in all involved meetings, origin and all targets.
