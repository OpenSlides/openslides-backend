## Payload
```
{
    motion_id: Id;
    support: boolean;
}
```

## Action
This adds (support=True) or removes (support=False) the request user from `motion/supporter_ids`. This action fails, if the supporter system is deactivated (`meeting/motions_supporters_min_amount` is 0) or the motion state's `state/allow_support` is false.

## Permissions
The request user generally needs `motion.can_support`.

However, if the meeting has `users_forbid_delegator_as_supporter` and the request user has his vote delegated in the meeting, he needs `motion.can_manage` instead.
