## Payload
```
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
Calculations pertaining to the validity of the data are expected to be carried out in the calling action.