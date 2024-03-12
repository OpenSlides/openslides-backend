## Payload 
Includes workflow_timestamp from Issue2112
```
{
// Required
    id: Id;

// Optional
    title: string;
    number: string;
    text: HTMLStrict;
    reason: HTMLStrict;
    amendment_paragraph: {
        [paragraph_number: number]: HTMLStrict
    }; // JSON Field
    modified_final_version: HTMLStrict;
    state_extension: string;
    recommendation_extension: string;
    category_id: Id;
    block_id: Id;
    supporter_meeting_user_ids: Id[];
    tag_ids: Id[];
    attachment_ids: Id[];
    workflow_id: Id;
    start_line_number: int;
    workflow_timestamp: timestamp;
}
```

## Action
The timestamp `last_modified` must be updated. If `workflow_id` is given, the state is reset to the first state of the workflow. The same logic as in [motion.set_state](motion.set_state.md) is executed to maybe update the fields `number` or `created`.

## Permissions
The request user must have `motion.can_manage` or `motion.can_manage_metadata` or be a submitter of this motion and the motion's state must have `allow_submitter_edit` set to true.

If the request user does not have `motion.can_manage`, the fields in the payload are restricted with a whitelist. These fields are contained, if:
- the request user is a submitter of this motion and the motion's state has `allow_submitter_edit` set to true:
    * `title`
    * `text`
    * `reason`
    * `amendment_paragraph`
- the request user has `motion.can_manage_metadata`:
    * `category_id`
    * `motion_block_id`
    * `origin`
    * `supporter_meeting_user_ids`
    * `recommendation_extension`
    * `start_line_number`
    * `workflow_timestamp`
