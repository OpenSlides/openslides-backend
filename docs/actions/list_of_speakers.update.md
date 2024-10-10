## Payload
```
{
// Required
    id: Id;

// Optional
    closed: boolean;
    moderator_notes: HTML;
}
```

## Action
Updates a list of speakers.

## Permissions
The request user needs `list_of_speakers.can_manage_moderator_notes` to set `moderator_notes` and
`list_of_speakers.can_manage` for all other fields.
