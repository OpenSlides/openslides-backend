## Payload
```
{ id: Id; }
```

## Action
Deletes the motion workflow and all linked states. If the workflow is set as a default workflow for the meeting (`meeting/motions_default_workflow_id` or `meeting/motions_default_amendment_workflow_id`), an error must be returned. This implies, that always one workflow has to exists.

If there exists a motion which is in the workflow, the deletion has to fail.

## Permissions
The request user needs `motion.can_manage`.
