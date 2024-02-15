## Payload
```
{
// Required
    name: string;
    workflow_id: Id;

// Optional
    recommendation_label: string;
    css_class: string;
    restrictions: string[];
    allow_support: boolean;
    allow_create_poll: boolean;
    allow_submitter_edit: boolean;
    allow_motion_forwarding: boolean;
    set_workflow_timestamp: boolean;
    set_number: boolean;
    show_state_extension_field: boolean;
    merge_amendment_into_final: number;
    show_recommendation_extension_field: boolean;
    first_state_of_workflow_id: Id;
}
```

## Action
Creates a new state for a workflow.

## Permissions
The request user needs `motion.can_manage`.
