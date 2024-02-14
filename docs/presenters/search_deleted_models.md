## Payload

```js
{
  collection: string,
  filter_string: string,
  meeting_id: Id,
}
```

## Presenter

Searches all deleted models of the given collection in the given meeting for the given filter string. The fields which
are searched differ from collection to collection:
```
{
  "assignment": ["title"],
  "motion": ["number", "title"],
  "user": [
    "username",
    "first_name",
    "last_name",
    "title",
    "pronoun",
    "structure_level",
    "number",
    "email",
  ],
}
```
These 3 are also the only allowed collections. The result list is returned as a mapping from the
model's id to the searched fields of the model (see above).

## Permissions

TODO
