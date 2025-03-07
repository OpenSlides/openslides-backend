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

// Non-model fields for customizing the agenda item creation, optional
    agenda_create: boolean;
    agenda_type: number;
    agenda_parent_id: number;
    agenda_comment: string;
    agenda_duration: number;
    agenda_weight: number;
    agenda_tag_ids: Id[];
}
```

## Action
Creates an assignment. For the agenda fields see [Agenda](https://github.com/OpenSlides/OpenSlides/wiki/Agenda#additional-fields-during-creation-of-agenda-content-objects).

## Permissions
The user needs `assignment.can_manage`.
