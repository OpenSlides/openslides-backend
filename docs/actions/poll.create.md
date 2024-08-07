## Payload

Helper Interface for options to create:
```
Interface Option {
    // Exactly one of text, content_object_id or poll_candidate_user_ids must be given
    text: string;  // topic-poll
    content_object_id: Fqid; // must be one of  user or motion.
    poll_candidate_user_ids: [user_ids]; // sorted list of user ids for candidate list election

    // Only for type==analog, optional votes can be given
    Y?: decimal(6); // Y, YN, YNA mode
    N?: decimal(6); // N, YN, YNA mode
    A?: decimal(6); // YNA mode
}}
```

Payload:
```
{
// Required
    title: string;
    type: string;
    pollmethod: string;

    meeting_id: Id;
    options: Option[]; // must have at least one entry.

// Optional
    content_object_id: Fqid;
    description: string;
    min_votes_amount: number;
    max_votes_amount: number;
    allow_multiple_votes_per_candidate: boolean;
    global_yes: boolean;
    global_no: boolean;
    global_abstain: boolean;
    onehundred_percent_base: string;

// Only for non analog types
    entitled_group_ids: Id[];

// Only for type==analog
    publish_immediately: boolean;

// Only for type==analog, optional votes can be given
    votesvalid?: decimal(6);
    votesinvalid?: decimal(6);
    votescast?: decimal(6);
    amount_global_yes?: decimal(6);
    amount_global_no?: decimal(6);
    amount_global_abstain?: decimal(6);
}
```

## Action
If an analog poll with votes is given, the state is set to `finished` if at least one vote value is given. if `publish_immediately` is true and some vote value is given, the state is set to `published`. All options given are created as instances of the `option` model. If some options have values (for analog polls), `vote` objects have to be created, one for each option and vote value (`Y`, `N`, `A`).

The options must be unique in the way that each non-empty `text` and non-empty `content_object_id` can only exists once. The `option/weight` has to be set in the order the options are given in the payload. A global option has to be created.

If the `type` is `pseudoanonymous`, `is_pseudoanonymized` has to be set to `true`.

If the `content_object_id` points to a `motion` and the `motion_state` of the motion misses `allow_create_poll`, it is forbidden to create a poll.

The `entitled_user_ids` may not contain the meetings `anonymous_group_id`.

## Permissions
The request user needs:
- `motion.can_manage_polls` if the poll's content object is a motion
- `assignment.can_manage` if the poll's content object is an assignment
- `poll.can_manage` else
