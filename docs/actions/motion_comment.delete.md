## Payload
```
{ id: Id; }
```

## Action
Deletes the comment.

## Permissions
The request user must have `motion.can_see`. In addition the request user
* needs to be in at least one of the groups in `motion_comment_section/write_group_ids`. Note that the meeting admin is implicit in these groups or
* the `motion_comment_section.submitter_can_write` flag, referenced by the `section_id`, is set and
  the request user is one of the submitters of the motion. The request user also must have the
  `motion.can_see` permission, but this is a fulfilled precondition, see above.

