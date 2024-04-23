## Payload
```
{
// Required
    title: string;
    meeting_id: Id;

// Optional
    number: string;
    additional_submitter: string;
    sort_parent_id: Id;
    category_id: Id;
    block_id: Id;
    supporter_meeting_user_ids: Id[]; // meeting user ids
    tag_ids: Id[];
    attachment_ids: Id[];


// Special logic given by the type of the motion
    text: HTML;
    amendment_paragraph: {
        [paragraph_number: number]: HTML;
    };  // JSON Field
    lead_motion_id: Id;
    statute_paragraph_id: Id;
    reason: HTML; // is required, if special settings are set

// Optional special fields, see notes below
    workflow_id: Id;
    submitter_ids: Id[];

// Non-model fields for customizing the agenda item creation, optional
    agenda_create: boolean;
    agenda_type: number;
    agenda_parent_id: number;
    agenda_comment: string;
    agenda_duration: number;
    agenda_weight: number;
}
```

## Action
Creates a new motion.

First, the type of the motion is identified by the values of `lead_motion_id`, `statute_paragraph_id`:

- A normal motion: None of the fields are given.
- An amendment: `lead_motion_id` is given.
- A statute amendment: `statute_paragraph_id` is given.

If `lead_motion_id` and `statute_paragraph_id` is given, it must result in an error. This is the logic for other fields depending on the motion type:

- normal motion:
  - `text` required
  -  error, if `amendment_paragraph` is given
- amendment:
  - `text` XOR `amendment_paragraph` required
- statute amendment:
  - `text` required
  -  error, if `amendment_paragraph` is given

`reason` is independent must be given, if `meeting/motions_reason_required` is true.

There are some fields that need special attention:
- `workflow_id`: If it is given, the motion's state is set to the workflow's first state. The workflow must be from the same meeting. If the field is not given, one of the three default (`meeting/motions_default_workflow_id`, `meeting/motions_default_amendment_workflow_id` or `meeting/motions_default_statute_amendment_workflow_id`) workflows is used depending on the type of the motion to create.
- `submitter_ids`: These are **user ids** and not ids of the `submitter` model. If nothing is given (`[]`), the request user's id is used. For each id in the list a `motion_submitter` model is created. The weight must be set to the order of the given list.
- `agenda_*`: See [Agenda](https://github.com/OpenSlides/OpenSlides/wiki/Agenda#additional-fields-during-creation-of-agenda-content-objects).

Another things to do when creating a motions:
- Set the field `sequential_number`: It is the `max+1` of `sequential_number` of all motions in the same meeting. If there are no other motions in this meeting (e.g. this is the first one), it gets 1.
- Set timestamps:
  - always set `last_modified` and `created` to the current timestamp
  - if the state pointed to by `first_state_id` of the given workflow has the flag `set_workflow_timestamp` set, also set `workflow_timestamp`to the current timestamp.
- Field `number`: Attention, it is a string, even if the field is named `number`. Note that the `number` must be unique within the meeting if it is set (so all numbers with length > 0 are unique). See the next paragraph how to get a value for `number`.

### Determinate a value for `number`
This is the procedure to determine what to set for the field `number`:
  * If `number` in the payload is a string with a length > 0, set it as the number and stop, but raise an error, if it exists.
  * if `meeting/motions_number_type` == `"manually"` or not `motion.state.set_number`: Stop. We should not set the number automatically
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
    * If the motion is an amendment (it has a lead motion), `number_value` is the maximum+1 of `number_value` of all lead_motion.amendments. If there are no other amendments, `number_value` is 1. Hint: To easily access the `number_value` of other motions, it can be saved into the Datastore.
    * Else if `meeting/motions_number_type` is `"per_category"`, choose the maximum+1 of `number_value` of all motions in the motions category. This includes the "None"-category; if the motion has no category, the maximum is choosen of all motions, that do not have a category. If there are no other motions, `number_value` is 1.
    * Else: Choose the maximum+1 of `number_value` of all lead motions. If there are no other lead motions, choose 1.
  * create `number` from `prefix` and `number_value`:
    * First, `number_value` is converted to the string `number_value_string` and potentially filled with leading zeros. The value `meeting/motions_number_min_digits` gives the amount of minimum digits. E.g. if `number_value` is 12 and `meeting/motions_number_min_digits=3`, the `number_value_string` is `"012"`. If `number_value` is 3582, the `number_value_string` is `"3582"`.
    * Set `number = f"{prefix}{number_value_string}"`
  * Remember: `number` must be unique. If a motion with this number already exists, increment `number_value` by one and go to the last step (the prefix is the same, the number incremented - try again).
  * If there is a unique `number`, save it into the motion. Done!
  * Note: The complete calculation is restricted to motions and other objects from the same meeting.
 
### Some examples for determinating the number. First comes the general setup and the test cases are numbered:

`meeting/motions_number_type="manually"`
1) Create a motion without a number in the payload. It now has a blank one.
2) Create two motion without a number in the payload. Both have a blank one.
3) Create two motion with the same number in the payload. The second one fails since numbers must be unique.

`meeting/motions_number_type="serially_numbered"`, `meeting/motions_number_min_digits=3`, `meeting/motions_number_with_blank=true`. Create three categories: `{name: "A", prefix: "A"}`, `{name: "B", prefix: "B"}`, `{name: "no prefix"}` (the last one has an empty prefix, see https://github.com/OpenSlides/OpenSlides/pull/5723). Make sure the state the motions get has `set_number=true`.
1) Create three motions with no number in the payloads and each motion assigned to one category in the order A, B, no prefix. The resulting numbers should be `A 001`, `B 002`, `003`.
2) Create a motion with category A, it should get `A 001`. Create a second motion with the number `B 002` in the payload. Create a third motion with category B and no number in the payload. It must get the number `B 003`.
3) Create a motion in category A. It must get `A 001`. Delete it and create a new motion in category A. It should also get `A 001`.

`meeting/motions_number_type="per_category"`, `meeting/motions_number_min_digits=3`, `meeting/motions_number_with_blank=false`. Create three categories: `{name: "A", prefix: "A"}`, `{name: "B", prefix: "B"}`, `{name: "no prefix"}`. Make sure the state the motions get has `set_number=true`.
1) Create two motions in category A. Than two motions in category B. Than two motions in category `no prefix`. The numbers must be `A001`, `A002`, `B001`, `B002`, `001` and `002`.
2) Create a motion without a category. It gets the number `001`. Set `meeting/motions_number_min_digits=1`. Create a plain motion. It must get the number `2`.

`meeting/motions_number_type="per_category"`, `meeting/motions_number_min_digits=3`, `meeting/motions_number_with_blank=true`, `meeting/motions_amendments_prefix="X-"`. Create a category: `{name: "A", prefix: "A"}`. Make sure the state the motions get has `set_number=true`.
1) Create a motion in category A. It must get `A 001`. Create two amendments (motions wiuth `lead_motion_id` set to the id of `A 001`). The numbers are `A 001 X-001` and `A 001 X-002`.
2) Do 1) again, but with `meeting/motions_number_with_blank=false` and `meeting/motions_number_min_digits=1`. The numbers are `A1`, `A1X-1`, `A1X-2`.
3) Do 1) again, but set `meeting/motions_number_with_blank=false` and `meeting/motions_number_min_digits=1` after creating the first lead motion. The numbers are `A 001`, `A 001X-1`, `A 001X-2`.
4) Do 1) again. Create a new motion without an identifier and no `lead_motion_id`. It gets the number `002`.

Repeat an autonumbering task from above, but set the states `set_number=false`. The motions should not get a number and have a blank one, if it was not provided in the payload.

## Permissions
The request user needs:
- `motion.can_manage` if he has his vote delegated and the meeting has `users_forbid_delegator_as_submitter`
- `motion.can_create_amendments` if `lead_motion_id` is given
- `motion.can_create` else

If the request user does not have `motion.can_manage`, the fields in the payload are restricted with a whitelist. These fields are contained:
- `meeting_id`
- `title`
- `text`
- `reason`
- `lead_motion_id`
- `amendment_paragraph`
- `category_id`
- `statute_paragraph_id`
- `workflow_id`

If `lead_motion_id` is given and `category_id` is empty, the value of `category_id` is set to the value of the lead motion.