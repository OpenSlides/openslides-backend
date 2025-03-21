## Payload

```js
{
  meeting_id: Id;    // required
  // optional
  committee_id: Id;  // target committee for cloned meeting 
  welcome_title: str;
  description: str;
  start_time: timestamp;
  end_time: timestamp;
  location: str;
  organization_tag_ids: List[Id];
  name: str;
  external_id: str;  // prevent duplicate external ids
  user_ids: Id[];
  admin_ids: Id[];
  set_as_template: boolean;  // default False
}
```

## Action

The meeting will be duplicated as it is including all its items. That means, that every motion, every topic, every mediafile, every assignment and so will be duplicated too. Users should not be duplicated, instead the existing users from the source meeting should be included in the new meeting as part of the default- or admin-group.
The users in user_ids/admin_ids will also be added to the default_group/admin_group of the new meeting. The difference is, that they don't have to be part of the source meeting.

If `set_as_template` is not true and there are no `admin_ids` in the payload and no admins in meeting that should be duplicated, there will be an error.

A differing committee_id can be given, otherwise the committee_id
will be cloned untouched. 

If an archived meeting is cloned, the created meeting will be active.

Checks whether the organization.limit_of_meetings is unlimited(=0) or lower than the active meetings in organization.active_meeting_ids and raises an exception otherwise.

Meetings that have `locked_from_inside` set to true can not be cloned.

### Pre Updating fields

The fields `welcome_title, description, start_time, end_time, location, organization_tag_ids, name, external_id` could be updated for the 
cloned meeting. If name is not updated this way, it gets the suffix _- Copy_.
If `external_id` is not given, the `external_id` will be set to None in the new meeting.
If set_as_template is given, template_for_organization_id has to be set to 1.

## Permission

It is not allowed to clone a meeting from a different committee if said meeting isn't a template.

Otherwise the request user only needs the CML `can_manage` in the target committee (where the meeting is created).

