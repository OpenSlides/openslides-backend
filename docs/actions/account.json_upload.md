### Includes changes of feature branch `los-extension`!

## Payload

Because the data fields are all converted from CSV import file, **they are all of type `string`**. 
The types noted below are the internal types after conversion in the backend. See [here](preface_special_imports#internal-types) for the representation of the types.
```js
{
    // required
    data: {
        // all optional, but see rules below
        username: object,  // unique username, info: generated, done or error
        first_name: string,
        last_name: string,
        email: string,
        title: string,
        pronoun: string,
        gender: string, // as defined in organization/genders, info: done or warning
        default_password: string,  // info: generated, done or warning
        is_active: boolean,
        is_physical_person: boolean,
        default_vote_weight: decimal(6),  // info: done or error
        saml_id: string,  // unique saml_id, info: new, done or error
    }[];
}
```
## Return value and object fields

Besides the usual headers as seen in payload (name and type), there are these differences:

- `username`: object with info "generated" or "done", depending on whether the username was generated or not.
- `saml_id`: object with info "new" if set for the first time or "done" if changed. "error" will be reported on duplicate "saml_ids.
- `default_password`: object with info "generated" or "done", depending on whether the default_password was generated or not. The info "warning" signalizes, that `default_password`, `password` and `can_change_own_password` will be removed by setting `saml_id`, because local login will not be possible anymore.
- `default_vote_weight` doesn't allow 0 values

The row state can be one of "new", "done" or "error". In case of an error, no import should be possible.

See [common description](preface_special_imports#general-format-of-the-result-send-to-the-client-for-preview).


## Action
The data will create or update users.

The data, enriched with building some field values and a first new column "state" from row state (`done`, `new`, `error`), is saved in an action worker. The action worker, its id and the preview data (without the new state column) are returned. For generating the preview data it is looked for errors.

### User matching

To decide whether to update an existing user with a row or to create a new one, the data is tried to match to the existing users analogously to the [`search_users` presenter](search_users#logic):
- If `username` is provided, it is only matched by username. All other data is ignored for the matching. If the username does not exist yet, a new user is created. If found add a new column with the Id to the data.
- If `saml_id` is provided, it is only matched by saml_id. All other data is ignored for the matching. If the saml_id does not exist yet, a new user is created. If found add a new column with the Id to the data.
- If `username` and `saml_id` are not provided, all of `first_name`, `last_name` and `email` must be provided instead. A user matches the row if all three fields are equal. In this case fill the `username` in data from db and a also add a column with the Id to data. If no user is found which matches the data, a new user is created and a username generated.

One of these cases must be true. If fewer fields are given than necessary (e.g. `first_name` is missing), no matching to existing users is done at all. Instead, a new user is created and a username generated. If both `first_name` and `last_name` are missing, the row is invalid since no username can be generated.

If `saml_id` is given, there may be no password, default_password or can_change_own_password for local user access set.

## Permission
Organization management level `can_manage_users`