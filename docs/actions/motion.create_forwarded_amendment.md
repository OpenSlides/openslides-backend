## Payload

```
{
  amendment_data: {
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
        with_change_recommendations: boolean;
        with_attachments: boolean;
  };

  forwarded_attachments?: {
    [target_meeting_id: number]: Set<origin_attachment_id>;
  };

  meeting_mediafile_replace_map?: {
    [origin_meeting_id: number]: {
      [origin_attachment_id: number]: target_attachment_id;
    };
  };
}
```

## Internal action

Forwards an amendment in a manner that is to what is done with normal motions in [motion.create_forwarded](motion.create_forwarded.md)

The only change is that the `with_amendments` flag is not in the payload, because it is assumed to be true.

## Custom `action_data` Structure

This action requires an `action_data` object with one required and up to two optional fields that should be passed only if `with_attachments === true`.

* **`amendment_data` _(required)_**: The actual action_data to be processed.

* **`forwarded_attachments` _(optional)_: `dict[int, set[int]]`**
  A mapping of already-forwarded attachments.
  Format: `{target_meeting_id: set of origin_attachment_ids}`
  These attachments were already forwarded during lead motion processing and should be **skipped** during further forwarding.

* **`meeting_mediafile_replace_map` _(optional)_: `dict[int, dict[int, int]]`**
  A nested mapping to track replaced media files.
  Format: `{origin_meeting_id: {origin_attachment_id: target_attachment_id}}`
  Used to assign the forwarded meeting_mediafiles to the corresponding target motions.
