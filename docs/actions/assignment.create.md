## Payload
```
{
// Required
    title: string;
    meeting_id: Id;

// Optional
    description: HTML;
    open_posts: number;
    phase: number;
    default_poll_description: string;
    number_poll_candidates: boolean;
    tag_ids: Id[];
    attachment_mediafile_ids: Id[];
}
```

## Action
Creates an assignment.

## Permissions
The user needs `assignment.can_manage`.
