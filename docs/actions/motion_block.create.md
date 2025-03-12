## Payload
```js
{
    title: string;
    internal: boolean;
    meeting_id: Id;

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
Creates a new motion block. For the agenda fields see [Agenda](https://github.com/OpenSlides/OpenSlides/wiki/Agenda#additional-fields-during-creation-of-agenda-content-objects).

## Permissions
The request user needs `motion.can_manage`.
