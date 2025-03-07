## Payload
```js
{
    // required
    collection: string,
    external_id: string,
    context_id: Id
}
```
## Returns
```js
{
    id: Id
}
```
in the case one id is found.
```js
{
    id: null,
    error: string
}
```
else.

## Logic

Searches for an `external_id` in the given collection (`group`, `meeting` or `committee`) in the respective context. `context_id` must point to the respective parent object: if the collection is `group`, this must be the `meeting_id`, for `meeting` it is the `committee_id` and for `committee` it must be `1` for the `orgnization_id`. If one id is found, return the id, else return an error and and `null` for the id.

Following error cases could be encountered: "No item with 'external_id' was found" and "More then one item with 'external_id' were found".

If the `group` collection is given, and there are locked meetings, the presenter will act as if these groups do not exist. They will not count towards the result.

For searching a user by `saml_id` see [search_users](search_users.md).

## Permissions
The request user needs OML `can_manage_organization`.
