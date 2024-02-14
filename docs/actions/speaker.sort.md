## Payload
```
{
    list_of_speakers_id: Id;
    speaker_ids: Id[];
}
```

## Action
Sorts all **waiting** speakers by `weight`. `speaker_ids` must include all waiting speakers of the list of speakers in the new order. The `weight` is set accordingly.

## Permissions
The request user needs `list_of_speakers.can_manage`.
