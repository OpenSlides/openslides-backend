## Payload
```
{
// Required
    meeting_id: Id;
    title: string;
    lead_motion_id: Id;
    origin_id: Id;

// Optional
    text: HTML;
    reason: HTML;
    amendment_paragraphs: JSON
    use_original_submitter: boolean;
    use_original_number: boolean;
}
```

## Internal action
Forwards an amendment in a manner that is to what is done with normal motions in [motion.create_forwarded](motion.create_forwarded.md)

The only change is that the `with_amendments` flag is not in the payload, because it is assumed to be true.