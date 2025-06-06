## Payload
```js
{ id: Id; }
```

## Action
Must recursively delete amendments, change recommendations, submitters, polls and comments.

## Permissions
The request user must have `motion.can_manage` or be a submitter of this motion and the motion's state must have `allow_submitter_edit` set to true.
