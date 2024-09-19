## Payload
```
{
// Required
    id: Id;

// Optional
    is_public: boolean;
    access_group_ids: Id[]
    inherited_access_group_ids: Id[]
}
```

## Internal action
The action updates a meeting_mediafile item. 
Calculations pertaining to the validity of the data are expected to be carried out in the calling action.