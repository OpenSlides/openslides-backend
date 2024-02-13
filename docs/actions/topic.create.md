## Payload
```
{
// Required
    title: string;
    meeting_id: Id;

// Optional
    text: HTML;
    attachment_ids: Id[];
    tag_ids: Id[];

    // Non-model fields for customizing the agenda item creation
    agenda_type: number;
    agenda_parent_id: number;
    agenda_comment: string;
    agenda_duration: number;
    agenda_weight: number;
}
```

## Action
Note: `attachment_ids` and `tag_ids` must be from the same meeting. For the agenda fields see [[Agenda#additional-fields-during-creation-of-agenda-content-objects]].

## Permissions
The request user needs `agenda_item.can_manage`.
