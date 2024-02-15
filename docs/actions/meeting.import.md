## Payload
```
{
  committee_id: Id;
  meeting: File; // JSON file with Object<MeetingImportData>
}
```

## Action

Import one meeting from a file. The file must only contain exactly one meeting.
- All previously used IDs (i.e motion sequential number) will be replace with new valid fqids.
- link to committee (`meeting/committee_id` and `committee/meeting_ids`)
- `meeting/enable_anonymous` will be disabled
- `meeting/imported_at` hints if and when the meeting was imported.
- The request user is assigned to the admin group.
- meeting.is_active_in_organization_id is set.
- It has to be checked, whether the organization.limit_of_meetings is unlimited(=0) or lower than the active meetings in organization.active_meeting_ids, if the new meeting is not archived (`is_active_in_organization_id` is set)
- Search for users and if username, first-name, last-name and email are identical use this user instead creating a duplicate. Keep the data, including password, of the exiating user.
- Users, that still have to be duplicated:
  - Imported usernames will be checked for uniqueness and adjusted in the case of collisions.
  - All previously set user passwords will be replaced


## Permissions
The user must be the committee manager of the given committee.

### Info

The `meeting` object must contain a valid `_migration_index` on root level.
