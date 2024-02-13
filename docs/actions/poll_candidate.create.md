## Payload

```
{
   // Required
   user_id: Id;
   poll_candidate_list_id: Id;
   weight: number;
}
```

## Action

Internal action to create a poll candidate with the `meeting_id` inferred from the `poll_candidate_list_id`.
