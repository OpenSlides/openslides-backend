## Payload
```js
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

    manager_ids: Id[];
// Group B
    forward_to_committee_ids: Id[];
    receive_forwardings_from_committee_ids: Id[];

// Group C
    parent_id: Id;

// Group D
    manager_ids: Id[];
}
```

## Action
Updates the committee.

The `default_meeting_id` must refer to a meeting of this committee.
Re-calculates `committee/all_parent_ids` from the new `parent_id` for this and all sub-models.

## Permissions
- Group A: The user needs the CML `can_manage` or the OML `can_manage_organization`
- Group B: The user needs the OML `can_manage_organization` or the CML `can_manage` for all target committees that were added/removed from the list and not `organization/restrict_edit_forward_committees` to be set.
- Group C: The user needs the OML `can_manage_organization` or the CML `can_manage` for a committee that is an _ancestor_ of the intended child committee and either the intended parent committee or one of its ancestors. Only organization managers may set this field to `None`.
- Group D: Like group A, except if `organization/restrict_editing_same_level_committee_admins` is true, the CML requirement will be further restricted to ancestor committee `can_manage`CMLs only. Users with no other admin permission than that of the edited committee will therefore not be allowed.
