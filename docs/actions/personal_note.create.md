## Payload
```
{
// required
    content_object_id: Fqid;

// At least one has to be given
    star: boolean;
    note: HTML;
}
```

## Action
The `personal_note/meeting_id` is set to the meeting id of the content object. The
`personal_note/meeting_user_id` is set to the `meeting_user` of the request user in the meeting
determined by the given `content_object_id`. Fails if there is already a personal note for the
content object and the user (`meeting_user_id` and `content_object_id` are unique together).

# Permissions
The user must be associated to the meeting and must not be the anonymous user.
