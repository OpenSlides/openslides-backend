## Payload

Because the data fields are all converted from CSV import file, **they are all of type `string`**. 
The types noted below are the internal types after conversion in the backend. See [here](preface_special_imports.md#internal-types) for the representation of the types.
```js
{
  // required
    data: {
      // required:
        name: string;
      // optional:
        description: string,
        forward_to_committees: string[],
        organization_tags: string[],
        managers: string[],
        meeting_name: string,
        meeting_start_time: date,
        meeting_end_time: date,
        meeting_admins: string[],
        meeting_template: string,
    }[]
}
```

All meeting fields are prefixed with `meeting_`. The fields `meeting_{start|end}_time` must be dates of the format `YYYY-MM-DD`.

## Return value

Besides the usual headers as seen in the payload (`name`, `type`, `is_list`), the following fields are of type [object](preface_special_imports.md#the-special-type-object) and have a corresponding `info` field with different meanings:
- `forward_to_committees`:
  - `done`: The committee was found in the datastore.
  - `new`: The committee will be created as part of this import.
  - `warning`: The committee was not found and will not be part of the import.
- `organization_tags`:
  - `done`: The tag was found in the datastore.
  - `new`: The tag will be newly created with color `#2196f3`.
- `managers`:
  - `done`: The user was found in the datastore.
  - `warning`: The user was not found and will not be part of the import.
- `meeting_admins`:
  - `done`: The user was found in the datastore.
  - `warning`: The user was not found and will not be part of the import.
  - `error`: Will be entered in extra object if no user was found here or in the optional templates admins
- `meeting_template`:
  - `done`: The meeting was found in the datastore, the new meeting will be cloned from it.
  - `warning`: The meeting was not found and the new meeting will not be cloned, but freshly created.

The fields `forward_to_committee`, `organization_tags`, `managers`, `meeting_admins` and `meeting_template` store the `id` of the related model, if it exists, in the object for the import.

The row state can be one of `new`, `done` or `error`. If it's `error`, no import should be possible.

The statistics part of the result:
```js
  total: int
  created: int
  updated: int
  error: int
  warning: int
  meetings_created: int
  meetings_cloned: int
  organization_tags_created: int
```
Rows with error state will not add onto the `meetings_created`, `meetings_cloned` and `organization_tags_created` statistic fields.
See [common description](preface_special_imports.md#general-format-of-the-result-send-to-the-client-for-preview).

## Action

The data will create or update committees. The committees will be identified by their exact name.
The fields `description`, `forward_to_committees`,`managers` and `organization_tags` belong to the committee and will be updated in an existing committee. This way forwardings, managers and organization tags can be added or removed.

Giving a `meeting_name` will always create a new meeting in the committee with the given name. If a `meeting_template` is given, this will be cloned, otherwise a fresh meeting will be created.

The data, enriched with building some field values and a first new column "state" from row state (`new`, `done`, `error`), is saved in an action worker. The action worker, its id and the preview data (without the new status column) are returned. For generating the preview data it is looked for errors.

### User matching

The users given in `managers` and `meeting_admins` will be matched only by username. The `saml_id` will not be used for the search.

## Permission

The request user needs OML `can_manage_organization`.
