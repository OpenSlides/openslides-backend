## Payload
```js
{
// Required
    id: Id,

// Optional, only if state == created
    pollmethod: string,
    min_votes_amount: number,
    max_votes_amount: number,
    max_votes_per_option: number,
    allow_multiple_votes_per_candidate: boolean,
    global_yes: boolean,
    global_no: boolean,
    global_abstain: boolean,
    backend: string,

// Optional, only if state == created, only for non analog types
    entitled_group_ids: Id[],

// Optional, every state
    title: string,
    description: string,
    onehundred_percent_base: string,

// type==analog, every state
    votesvalid?: number,
    votesinvalid?: number,
    votescast?: number,
    publish_immediately: boolean,

// action called internally
    entitled_users_at_stop: json
}
```

## Action
For analog polls: If the state is created and at least one vote value is given (`votesvalid`/`votesinvalid`/`votescast`), the state must be set to finished. if additionally `publish_immediately` is given, the state must be set to published.

For electronic polls some fields can only be updated, if the state is *created*.

The `entitled_group_ids` may not contain the meetings `anonymous_group_id`.

The `max_votes_per_option` and `min_votes_amount` must be smaller or equal to `max_votes_amount` after the model had been updated.

## Permissions
The request user needs:
- `motion.can_manage_polls` if the poll's content object is a motion
- `assignment.can_manage` if the poll's content object is an assignment
- `poll.can_manage` if the poll's content object is a topic
