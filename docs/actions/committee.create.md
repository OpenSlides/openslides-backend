## Payload
```js
{
// Required
    name: string;
    organization_id: Id;

// Optional
    description: HTML;
    organization_tag_ids: Id[];
    external_id: string;
    parent_id: Id;

    manager_ids: Id[];

    // Needs parent_id set and manage rights for all target committees
    forward_to_committee_ids: Id[];
    receive_forwardings_from_committee_ids: Id[];
    forward_agenda_to_committee_ids: Id[];
    receive_agenda_forwardings_from_committee_ids: Id[];
}
```

## Action
Creates the committee.
Calculates `committee/all_parent_ids` from the `parent_id`.

## Permissions
The user needs to have the organization management level `can_manage_organization`.
If a `parent_id` is given, CML `can_manage` for an ancestor committee will also suffice.
