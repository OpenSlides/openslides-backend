## Payload
```
{
// Required
    id: number;

// Optional
    title: string;
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
Updates an assignment.

## Permissions
The user needs `assignment.can_manage`.
