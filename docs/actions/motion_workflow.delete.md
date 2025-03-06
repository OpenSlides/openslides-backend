## Payload
```
{ id: Id; }
```

## Action
Deletes the motion workflow and all linked states. If the workflow is set as a default workflow for the meeting (`meeting/motions_default_workflow_id` or `meeting/motions_default_amendment_workflow_id`), an error is returned. This means, that one workflow always needs to exists.

If there is a motion using the workflow, the deletion has to fail.

## Permissions
The request user needs `motion.can_manage`.
