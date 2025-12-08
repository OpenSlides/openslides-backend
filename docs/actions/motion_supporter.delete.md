## Payload
```js
{
    id: Id;
}
```

## Action
Deletes a motion_supporter.
With the exception of internal calls (for the sake of merge), this action fails in two cases:
- the supporter system is deactivated (`meeting/motions_supporters_min_amount` is 0)
- the motion state's `state/allow_support` is false and the calling user does not have `motion.can_manage_meta_data` permission.

## Permissions
The request user generally needs `motion.can_manage_metadata`.

If he is removing his own support and either `users_forbid_delegator_as_supporter` is turned off for the meeting or he does not have his vote delegated, `motion.can_support` will also suffice.
