(NOT IMPLEMENTED)

## Payload
```
{
  to_committee_id: Id;
  from_committee_id: Id;
  name: string;
}
```

## Action
This action "clones" a meeting from the source `from_committee_id` (`committee/template_meeting_id`) into the target `to_committee_id`. It raises an error, if the source has no template meeting (`committee/template_meeting_id`). The meeting has to be cloned, and everything in it, too. This means, that a new meeting is created, with the `name` given from the payload. The every field form the template meeting is copied. Every model in the meeting is duplicated (every motion, topic, projector, ...) and assigned to the new meeting. At the end, there is a full clone of the old meeting. Especially every model gets new ids.

If the template meeting was archived the resulting target meeting should be set active (unarchived). 

It has to be checked whether the `organization.limit_of_meetings` is unlimited (`0`) or lower than
the amount of active meetings in `organization.active_meeting_ids` if the new meeting is not archived
(`is_active_in_organization_id` is set).

## Permissions
A user must be the committee manager of the committee of the meeting (CML `can_manage`).
