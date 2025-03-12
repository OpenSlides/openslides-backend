## Payload
```js
{
// Required
    name: string;
    organization_id: Id;

// Optional
    description: HTML;
    manager_ids: Id[];
    organization_tag_ids: Id[];
    forward_to_committee_ids: Id[];
    receive_forwardings_from_committee_ids: Id[];
    external_id: string;
}
```

## Action
Creates the committee.

## Permissions
The user needs to have the organization management level `can_manage_organization`.
