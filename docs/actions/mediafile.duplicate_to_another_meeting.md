## Payload
```js
{
// Required
    id: Id;
    owner_id: Fqid;
    origin_id: Id;

// Optional
    parent_id: Id;
}
```

## Internal action
The action duplicates a mediafile item along with the a corresponding medifile in the mediaservice.

The following properties are copied from the origin mediafile (with id equal to `origin_id`) to the new mediafile: `title`, `is_directory`, `filesize`, `filename`, `mimetype`, `pdf_information`.

This action does not generate an ID normally and requires a reserved ID to be provided for each instance.
