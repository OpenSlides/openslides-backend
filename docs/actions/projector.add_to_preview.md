## Payload
```js
{
    // required
    ids: Id[] // projector ids
    content_object_id: Id;
    meeting_id: Id;

    // optional
    options: JSON;
    stable: boolean;
    type: string;
}
```

## Action
This action has the same payload as projector.project, but it adds the implied projection to the end of each projector's preview. Each projection gets the weight of max(weight)+1 per projector preview.

## Permissions
The request user needs `projector.can_manage`
