## Payload
```
{
  committee_id: Id;
  meeting: File; // JSON file with Object<MeetingImportData>
}
```

## Action

Imports one meeting from a file. The file must only contain exactly one meeting.
- All previously used IDs (i.e motion sequential number) are replaced with new valid fqids.
- link to committee (`meeting/committee_id` and `committee/meeting_ids`)
- `meeting/enable_anonymous` is disabled
- `meeting/imported_at` hints if and when the meeting was imported.
- The request user is assigned to the admin group.
- meeting.is_active_in_organization_id is set.
- Checks, whether the organization.limit_of_meetings is unlimited(=0) or lower than the active meetings in organization.active_meeting_ids, if the new meeting is not archived (`is_active_in_organization_id` is set)
- Searches for users and if username, first-name, last-name and email are identical uses this existing user instead of creating a duplicate. Keeps the data, including password, of the existing user. Relevant relations such as to the meeting are updated though.
- For users that still have to be duplicated:
  - Imported usernames are checked for uniqueness and adjusted in case of collisions.
  - All previously set user passwords are replaced
- Genders are only updated or imported if a new user needs to be created. Updated users retain their pre-existing gender.
- Meeting external_ids can not exist in other meetings, if they do, an exception is raised.
- All references to other meetings and their models (like `motion/all_origin_ids` for example) are removed


## Permissions
The user must be the committee manager of the given committee.

### Info

The `meeting` object must contain a valid `_migration_index` on root level.
The `meeting` object cannot have `locked_from_inside` set to true.
