## Payload
Because the data fields are all converted from CSV import file, **they are all of type `string`**. 
The types noted below are the internal types after conversion in the backend. See [here](preface_special_imports.md#internal-types) for the representation of the types.
```js
{
     // required
     meeting_id: Id,
     data: {
          // all optional, but see rules below
          username: string,  // unique username, info: generated, new (changed via member_number matching), done or error (first-/last-name), done (used the given username), remove(missed field permission)
          first_name: string,  // info: done or remove (missing field permission)
          last_name: string,  // info: done or remove (missing field permission)
          email: string,  // info: done, error or remove (missing field permission)
          member_number: string, // unique member_number, info: done, error, new (newly added) or remove (missing field permission)
          title: string,  // info: done or remove (missing field permission)
          pronoun: string,  // info: done or remove (missing field permission)
          gender: string, // as defined in organization/genders, info: done, warning (undefined gender) or remove (missing field permission)
          default_password: string,  // info: generated, done, warning or remove (missing field permission)
          is_active: boolean,  // info: done or remove (missing field permission)
          is_physical_person: boolean,  // info: done or remove (missing field permission)
          structure_level: string,  // info: done, new or remove (missing field permission)
          number: string,  // info: done or remove (missing field permission)
          vote_weight: decimal(6),  // info: done, error or remove (missing field permission)
          comment: string,  // info: done or remove (missing field permission)
          is_present: boolean,  // info: done or remove (missing field permission)
          groups: string[],  // info per item: done, warning, generated
          saml_id: string,  // unique saml_id, info: new, warning, error, done or remove (missing field permission)
     }[],
}
```
## Objects (fields with additional info) in the resulting preview-data

See general user fields in [account.json_upload#user-matching](account.json_upload.md#user-matching) with some additions:
- `groups`: object with info "warning" for not found groups, "done" for a found group. If there is no group found at all, the default group will added automatically with state "generated".
- `vote_weight` doesn't allow 0 values
- `structure_level` will return `new` if it is not found, in such cases the structure level will be created in the import
- All fields that could be removed by missing permission could have the state "remove" (will be
  removed on import) or "done" (will be imported). See `info` note in payload above for affected
  fields.

## Action

Basically does the same as [account.json_upload](account.json_upload.md) with a few different and
meeting-specific fields, such as groups.

**Important note**: The `groups` from the payload will override all current groups of the user in
the given meeting, meaning that this import can be used to remove users from groups. If no groups
are given, the user will be added to the default group of the meeting.

The field `is_present` is a boolean in the payload. When importing this data, the actual user field
`is_present_in_meeting_ids` will be modified based on its value.

Structure levels will be created during the later import phase if they aren't found.
For this purpose the statistics row includes an extra point 'structure levels created'

### User matching
Same as in [account.json_upload#user-matching](account.json_upload.md#user-matching)

## Backend interna
This action is the first part of the actions for the import of participants (mean: users in a meeting).
It should use the `JsonUploadMixin` and is a single payload action.

The `groups` field includes a list of group names. The group names will be looked up in the meeting.
If a group is found, info will be *done* and id is the id of the group. If no group is found, info will be *warning*.
If no group in groups is found at all, the entry state will be *error* and import shouldn't be possible.

It checks the data and creates an import_preview-collection with modified data (uses: `store_rows_in_the_import_preview`).

And returns (with `create_action_result_element`):
```python
{
     "id": self.new_store_id, // action_worker id
     "headers": self.headers, // headers information
     "rows": self.rows, // modified data
     "statistics": self.statistics,  // some calculated int with description
     "state": self.state, // state
}
```
The headers information is derived from the payload. 
The statistics should be:
```
 Row errors: x
 Participants created: x
 Participants updated: x
```

The `structure_level` will have to be matched to an existing structure level, if it exists, or
otherwise a new one has to be created.

## Permission
Permissions are analogue to `user.create` and `user.update`. The `saml_id` can be used in import, because user.create/.update will be used internal.

In case of an update, remove fields from the payload that don't change the content compared to database to avoid unnecessary
permission errors. Don't forget the special permissions for `default_password` on `user.update`.
Anyway the user must have the permission `user.can_manage`, `cml.can_manage` or >= `oml.can_manage_users`. Otherwise the whole import will be finished with an exception.