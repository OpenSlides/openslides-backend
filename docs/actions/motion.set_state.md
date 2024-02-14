## Payload
```
{
    id: Id;
    state_id: Id;
}
```

## Action
The `state_id` must be a next or previous state as the current motions state, except if the request user has `motion.can_manage_metadata`, in which case all states of the same workflow are valid.

The field `workflow_timestamp` must be set to the current timestamp if it is currently empty and the
new state has the `set_workflow_timestamp` flag.

The field `number` is potentially updated from the motion. This procedure diverges slightly from the [motion.create](motion.create.md) one, but is essentially equal. Diverging steps are marked with CHANGED/NEW. This is the procedure to determine what to set for the field `number`:
  * If the motion already has a non-empty `number` or `meeting/motions_number_type` == `"manually"` or not `state.set_number`: Stop. We should not set the number automatically
  * A _prefix_ is created:
    * If the motion is an amendment (it has a lead motion), the prefix is:
      ```
      if meeting/motions_number_with_blank:
          prefix = f"{lead_motion.number} {meeting/motions_amendments_prefix}"
      else:
          prefix = f"{lead_motion.number}{meeting/motions_amendments_prefix}"
      ```
    * Else if the motion has a category, the prefix is:
      ```
      if meeting/motions_number_with_blank:
          prefix = f"{category.prefix} "
      else:
          prefix = f"{category.prefix}"
      ```
    * Else, the prefix is an empty string
  * choose a _number_value_. This is a numerical variable with the actual numerical number:
    * If the motion already has a `number_value`, choose it. (<-- NEW)
    * Else if the motion is an amendment (it has a lead motion), `number_value` is the maximum+1 of `number_value` of all lead_motion.amendments. If there are no other amendments, `number_value` is 1. Hint: To easily access the `number_value` of other motions, it can be saved into the Datastore.
    * Else if `meeting/motions_number_type` is `"per_category"`, choose the maximum+1 of `number_value` of all motions in the motions category. This includes the "None"-category; if the motion has no category, the maximum is choosen of all motions, that do not have a category. If there are no other motions, `number_value` is 1.
    * Else: Choose the maximum+1 of `number_value` of all motions. If there are no other motions, choose 1.
  * create `number` from `prefix` and `number_value`:
    * First, `number_value` is converted to the string `number_value_string` and potentially filled with leading zeros. The value `meeting/motions_number_min_digits` gives the amount of minimum digits. E.g. if `number_value` is 12 and `meeting/motions_number_min_digits=3`, the `number_value_string` is `"012"`. If `number_value` is 3582, the `number_value_string` is `"3582"`.
    * Set `number = f"{prefix}{number_value_string}"`
  * Remember: `number` must be unique. If a motion with this number already exists, increment `number_value` by one and go to the last step (the prefix is the same, the number incremented - try again).
  * If there is a unique `number`, save it into the motion. Done!
  * Note: The complete calculation is restricted to motions and other objects from the same meeting.

## Permissions
The request user needs to have `motion.can_manage_metadata`. Or he must be the submitter of the motion and the motion's state must have `allow_submitter_edit` set to true.
