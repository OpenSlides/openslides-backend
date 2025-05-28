## Payload

```js
{
  // required
  permission_type: "meeting" | "committee" | "organization"
  permission_id: number,    // Id of permission scope object
  search: {
    "username": string,
    "saml_id": string,
    "first_name": string,
    "last_name": string,
    "email": string,
    "member_number": string
  }[]
}
```
## Returns

```js
{
  "id": number,
  "username": string,
  "saml_id": string,
  "first_name": string,
  "last_name": string,
  "email": string,
  "member_number": string
}[][]
```
A double array: The outer array has the same length as the request's `search` array and contains
exactly one entry (nested array) for each search entry, in the same order. Each nested array
represents all users which matched the search entry with the given object of 6 fields.

## Logic

The matching is performed independently per search entry. If a `username` is given, the other fields
are ignored and users are only matched by `username`. If the `username` is empty, the users are only matched by `saml_id`. If the `saml_id` is empty, the users are only matched by `member_number`. If the `member_number` is also empty all other fields (`first_name`, `last_name`, `email`) must match instead.

## Permissions

The necessary permission is part of the payload and send in the permission fields. You should define
it in context of your search, i.e. do you want to add a user to a meeting use the scope of that
meeting; do you look for a committee manager, you should give him a committee scope. The permission
scope consists of a `permission_type` from enum `UserScope` and the `permission_id` of the object.
