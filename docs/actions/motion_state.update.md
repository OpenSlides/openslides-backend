## Payload
```
{
// Required
    id: Id;

// Optional
    name: string
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
    weight: number;

    next_state_ids: Id[];
    previous_state_ids: Id[];
}
```

## Action
All ids in `next_state_ids`/`previous_state_ids` must belong to the same workflow (this is not a tree, but a graph, so no checks for cycles, or any special checks).

## Permissions
The request user needs `motion.can_manage`.
