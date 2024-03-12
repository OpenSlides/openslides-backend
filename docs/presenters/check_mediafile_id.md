# Payload

```
{
    mediafile_id: Id
}
```

# Returns

```
{
    ok: True,
    filename: string,
}
```
or `{ok: False}` on errors

# Logic

This presenter is called by the mediaservice, so it can get check permissions and get the filename of the mediafile.

On every error `{ok: False}` is returned. The presenter fetches the mediafile with the given id. It is checked that is exists and is not a directory. If it exists, there are three possibilities:

- Meeting-wide mediafile: Permissions are checked to determine whether the user can see the mediafile. This is the same logic as the see-property in the [Mediafile restrictions](https://github.com/OpenSlides/openslides-autoupdate-service/blob/main/internal/restrict/collection/mediafile.go). If everything is fine, the filename is returned to the caller.
- Organization-wide mediafile:
  - without a `token`: If the user is logged in, return the filename.
  - with a `token`: The filename is the `token` with the extension guessed from the `mimetype`. Even users which are not logged in can see these mediafiles.