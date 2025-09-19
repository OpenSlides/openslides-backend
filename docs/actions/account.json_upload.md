## Payload

Because the data fields are all converted from CSV import file, **they are all of type `string`**. 
The types noted below are the internal types after conversion in the backend. See [here](preface_special_imports.md#internal-types) for the representation of the types.
```js
{
    // required
    data: {
        // all optional, but see rules below
        username: object,  // unique username, info: generated, new (changed via member_number matching), done or error
        first_name: string,
        last_name: string,
        email: string, // info: done or error
        member_number: string, // unique member_number, info: done (used as matching field), new (newly added) or error
        title: string,
        pronoun: string,
        gender: string, // info: done or warning
        default_password: string,  // info: generated, done or warning
        is_active: boolean,
        is_physical_person: boolean,
        default_vote_weight: decimal(6),  // info: done or error
        saml_id: string,  // unique saml_id, info: new, done or error
        home_committee: string, // info: done, error, generated or remove (missing field permission)
        external: boolean // info: done, error, generated or remove (missing field permission)
    }[];
}
```
## Return value and object fields

Besides the usual headers as seen in payload (name and type), there are these differences:

- General user fields (shared between all user imports):
    - `username`: object with info "generated", "new" or "done", depending on whether the username was generated or not. The username may be overwritten when matching via the `member_nubmer`, then the info will be "new"
    - `saml_id`: object with info "new" if set for the first time or "done" if changed. "error" will be reported on duplicate "saml_ids.
    - `default_password`: object with info "generated" or "done", depending on whether the default_password was generated or not. The info "warning" signalizes, that `default_password`, `password` and `can_change_own_password` will be removed by setting `saml_id`, because local login will not be possible anymore.
    - `email` must be a valid email
    - `member_number`: object with info "new" or "done", depending on whether the member number will be newly added to an existing user or not. Overwriting a pre-existing value is not permitted and "error" will be used if it is tried. "error" will also be used if the member_number is not unique or matches a different user than the other matching criteria
    - `default_vote_weight` doesn't allow 0 values
    - `home_committee` points to the `user/home_committee_id` field and references an existing committee. Will be marked as `error` if it is not found. Marked as `remove` if the caller lacks necessary permissions to change it (see user.update doc for the correct permissions), this means it will be ignored upon import, unless the permissions change. Will receive an empty value with a `generated` state if `external` is set to true, since the field will be unset if that succeeds.
    - `external` will be `error` if the value is true and the caller is also trying to set `home_committee_id`, it is marked as `remove` if the caller lacks permission to set it (see user.update doc for the correct permissions) and it will be set to false and marked as `generated` if home committee is set and the field is empty.


The row state can be one of "new", "done" or "error". In case of an error, no import should be possible.

See [common description](preface_special_imports.md#general-format-of-the-result-send-to-the-client-for-preview).


## Action
The data will create or update users.

The data, enriched with building some field values and a first new column "state" from row state (`done`, `new`, `error`), is saved in an action worker. The action worker, its id and the preview data (without the new state column) are returned. For generating the preview data it is looked for errors.

### User matching

To decide whether to update an existing user with a row or to create a new one, the data is tried to match to the existing users:
- `member_number`, if given, is the preferred matching field. If there is a member_number and it fits a user, that user will be selected.

If nothing is found in this manner, a matching user will be sought analogously to the [`search_users` presenter](search_users.md#logic):
- If `username` is provided, it is only matched by username. All other data is ignored for the matching. If the username does not exist yet, a new username is created.
- If `saml_id` is provided, it is only matched by saml_id. All other data is ignored for the matching. If the saml_id does not exist yet, a new user is created. If found add a new column with the Id to the data.
- If `username` and `saml_id` are not provided, all of `first_name`, `last_name` and `email` must be provided instead. A user matches the row if all three fields are equal. In this case fill the `username` in data from db and a also add a column with the Id to data. If no user is found which matches the data, a new user is created and a username generated.

If the user is found, a new column with the Id is added to the data and to the object in the main matching field by which the import of the row will be calculated:
- `member_number` if the user was matched via `member_number`
- else `username`

One of these cases must be true. If fewer fields are given than necessary (e.g. `first_name` is missing), no matching to existing users is done at all. Instead, a new user is created and a username generated. If both `first_name` and `last_name` are missing, the row is invalid since no username can be generated.

If `saml_id` is given, there may be no password, default_password or can_change_own_password for local user access set.

## Permission
Organization management level `can_manage_users`