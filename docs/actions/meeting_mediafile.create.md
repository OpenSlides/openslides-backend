## Payload
```js
{
// Required
    mediafile_id: Id;
    meeting_id: Id;
    is_public: boolean;

// Optional
    access_group_ids: Id[]
    inherited_access_group_ids: Id[]
}
```

## Internal action
The action creates a meeting_mediafile item. 
Calculations pertaining to the validity of the data are mostly expected to be carried out in the calling action.
The only exceptions are, that the action will raise exceptions if:
- The mediafile is an unpublished organization file, or
- The mediafile already has a meeting_mediafile in this meeting.
