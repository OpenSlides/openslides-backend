## Payload
```
{
    name: string;
    meeting_id: Id;
}
```

## Action
Creates a new motion workflow. A default `motion_workflow/first_state_id` must be created with the name `default state`.

## Permissions
The request user needs `motion.can_manage`.
