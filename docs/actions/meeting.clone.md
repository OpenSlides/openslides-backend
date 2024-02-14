## Payload

```js
{
  meeting_id: Id;    // required
  committee_id: Id;  // optional: target committee for cloned meeting
  welcome_title: str;
  description: str;
  start_time: timestamp;
  end_time: timestamp;
  location: str;
  organization_tag_ids: List[Id];
  name: str;
  user_ids: Id[];
  admin_ids: Id[];
  set_as_template: boolean;  // default False
}
```

## Action

The meeting will be duplicated as it is including all its items. That means, that every motion, every topic, every mediafile, every assignment and so will be duplicated too. Users should not be duplicated, instead the existing users from the source meeting should be included in the new meeting as part of the default- or admin-group.
The users in user_ids/admin_ids will also be added to the default_group/admin_group of the new meeting. The difference is, that they don't have to be part of the source meeting.

A differing committee_id can be given, otherwise the committee_id
will be cloned untouched. 

It has to be checked, whether the organization.limit_of_meetings is unlimited(=0) or lower than the active meetings in organization.active_meeting_ids, if the new meeting is not archived (`is_active_in_organization_id` is set)

### Pre Updating fields

The fields `welcome_title, description, start_time, end_time, location, organization_tag_ids, name` could be updated for the 
cloned meeting. If name is not updated this way, it gets the suffix _- Copy_.
If set_as_template is given, template_for_organization_id has to be set to 1.

## Permission

The request user must have the CML `can_manage` in the target committee (where the meeting is created).