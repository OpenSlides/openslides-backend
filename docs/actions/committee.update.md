## Payload
```
 {
// Required
    id: number;

// Optional
// Group A
    name: string;
    description: HTML;
    default_meeting_id: Id;
    organization_tag_ids: Id[];
    external_id: string;

// Group B
    manager_ids: Id[];
    forward_to_committee_ids: Id[];
    receive_forwardings_from_committee_ids: Id[];
}
```

## Action
Updates the committee.

The `default_meeting_id` must refer to a meeting of this committee.

## Permissions
- Group A: The user needs the CML `can_manage` or the OML `can_manage_organization`
- Group B: The user needs the OML `can_manage_organization`
