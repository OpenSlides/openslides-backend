## Payload

```
{
    saml_id: string, // required
    title: string,
    first_name: string,
    last_name: string,
    email: string,
    gender: string,
    pronoun: string,
    is_active: boolean,
    is_physical_person: boolean,
}
```

## Action
The attributes for the payload are all configured in organization-wide settings. The configuration consists of a list of source attribute - target attribute pairs, where the target attributes are the ones documented in the payload.
Creates or updates the saml-account, depending whether the given `saml_id` exists or not. The `saml_id` is guaranteed to be unique in the whole system. If a gender does not exist in the collection, it will be created. The other fields will be set on creation or update.
The action must be `STACK_INTERNAL`. It should be called only from the auth service.

Extras to do on creation:

- As the field `username` is required, we copy the `saml_id` from payload to the `username` field, if the account will be created. Check and append the `username` with a current number to be unique.

- On creation the following fields will be set different from their default values:

    - `password`: do not fill
    - `default_password`: do not fill
    - `can_change_own_password`: `False`

    As you can see there is no password for local login and the user can't change it.

- Add user to the meeting by adding him to the group given in the organization-wide field-mapping as `"meeting": { "external_id": "xyz", "external_group_id": "delegates"}` if a `meeting`-entry is given. If it fails for any reason, a log entry is written, but no exception thrown. Add the user always to the group, if it fails try to add him to the default group.

## Return Value

The action always returns the `user_id` in the response object in `response.json["results"][0][0]['user_id']`

## Permissions
This action can be called only from inside the stack. This will be done from the auth service on login of a user for OpenSlides. There are no more permissions required.
