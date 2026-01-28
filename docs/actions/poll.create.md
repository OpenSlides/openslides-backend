## Payload

Helper Interface for options to create:
```js
Interface Option {
    // Exactly one of text, content_object_id or poll_candidate_user_ids must be given
    text: string,  // topic-poll
    content_object_id: Fqid, // must be one of  user or motion.
    poll_candidate_user_ids: [user_ids], // sorted list of user ids for candidate list election

    // Optionally and only for type==analog, votes can be given
    Y: decimal(6), // Y, YN, YNA mode
    N: decimal(6), // N, YN, YNA mode
    A: decimal(6)  // YNA mode
}
```

Payload:
```js
{
// Required
    title: string,
    type: string,
    pollmethod: string,

    meeting_id: Id,
    options: Option[], // must have at least one entry.

// Optional
    content_object_id: Fqid,
    description: string,
    min_votes_amount: number,
    max_votes_amount: number,
    max_votes_per_option: number,
    global_yes: boolean,
    global_no: boolean,
    global_abstain: boolean,
    onehundred_percent_base: string,
    backend: string,

// Optional, only for type==named
    live_voting_enabled: boolean,

// Only for non analog types
    entitled_group_ids: Id[],

// Only for type==analog
    publish_immediately: boolean,

// Optionally and only for type==analog, votes can be given
    votesvalid: decimal(6),
    votesinvalid: decimal(6),
    votescast: decimal(6),
    amount_global_yes: decimal(6),
    amount_global_no: decimal(6),
    amount_global_abstain: decimal(6)
}
```

## Action
If an analog poll with votes is given, the state is set to `finished` if at least one vote value is given. if `publish_immediately` is true and some vote value is given, the state is set to `published`. All options given are created as instances of the `option` model. If some options have values (for analog polls), `vote` objects have to be created, one for each option and vote value (`Y`, `N`, `A`).

The options must be unique in the way that each non-empty `text` and non-empty `content_object_id` can only exist once. The `option/weight` is set in the order the options are given in the payload. A global option is created.

If the `type` is `pseudoanonymous`, `is_pseudoanonymized` is set to `true`.

If the `content_object_id` points to a `motion` and the `motion_state` of the motion misses `allow_create_poll`, it is forbidden to create a poll.

The `entitled_group_ids` may not contain the meetings `anonymous_group_id`.

The `max_votes_per_option` and `min_votes_amount` must be smaller or equal to `max_votes_amount`.

The `live_voting_enabled` could be set for named votes and
(motion or assignment polls). Assignment polls need pollmethod `Y` and not
`global_yes` and `max_votes_amount` of 1.

## Permissions
The request user needs:
- `motion.can_manage_polls` if the poll's content object is a motion
- `assignment.can_manage_polls` if the poll's content object is an assignment
- `poll.can_manage` if the poll's content object is a topic
