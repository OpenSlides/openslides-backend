## Payload

Payload:
```
{
    // Required
    option_id: Id,
    meeting_id: Id,
    entries: [{
        user_id: Id,
        weight: number
    }]
}
```

## Internal action
Creates poll candidates for the entries and creates a `poll_candidate_list`. 
