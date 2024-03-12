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

## Action
Internal action. It creates poll candidates for the entries and creates a `poll_candidate_list`. 
