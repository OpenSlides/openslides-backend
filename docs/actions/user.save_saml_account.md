## Payload

```js
{
    saml_id: string, // required
    title: string,
    first_name: string,
    last_name: string,
    email: string,
    gender: string,
    pronoun: string,
    is_active: boolean,
    is_physical_person: boolean,
    member_number: string,
    // Additional meeting related data can be given. See below explanation on meeting mappers.
}
```

## Action
The attributes for the payload are all configured in organization-wide settings. The configuration consists of a list of source attribute - target attribute pairs, where the target attributes are the ones documented in the payload.
Creates or updates the saml-account, depending whether the given `saml_id` exists or not. The `saml_id` is guaranteed to be unique in the whole system. If a gender does not exist in the collection, it will be created. The other fields will be set on creation or update.
The action must be `STACK_INTERNAL`. It should be called only from the auth service.

Extras to do on creation:

- As the field `username` is required, we copy the `saml_id` from payload to the `username` field, if the account will be created. Check and append the `username` with a current number to be unique.

- On creation the following fields will be set different from their default values:

    - `password`: do not fill
    - `default_password`: do not fill
    - `can_change_own_password`: `False`

    As you can see there is no password for local login and the user can't change it.

### Meeting Mappers
- The saml attribute mapping can have a list of 'meeting_mappers' that can be used to assign users meeting related data. (See example below. A full example can be found in the [organization.update.md](organization.update.md))
    - A mapper can be given a 'name' for debugging purposes.
    - The 'external_id' maps to the meeting and is required (logged as warning if meeting does not exist). Multiple mappers can map to the same meeting.
    - If 'allow_update' is set to false, the mapper is only used if the user does not already exist. If it is not given it defaults to true.
    - Mappers are only used if every condition in the list of 'conditions' resolves to true. For this 
        - the value for 'attribute' in the payload data has to match the string or regex given in 'condition'. 
        - if no condition is given this defaults to true. 
        - lists in the SAML data are checked item by item if any of them matches. 
        - if the data is not a string, then it will be cast to a string for this purpose. F.e. "True", "4" and so on.
    - The actual mappings are objects or lists of objects of attribute-default pairs (exception: 'number', which only has the option of an attribute). 
        - The attribute refers to the payloads data.
        - A default value can be given in case the payloads attribute does not exist or contains no data. (Logged as debug)
        - Groups and structure levels are given as a list of attribute-default pairs.
- On conflict of multiple mappers mappings on a same meetings field the last given mappers data for that field is used. Exception to this are groups and structure levels. Their data is combined. 
- Values for groups and structure levels can additionally be given in comma separated lists composed as a single string.
- Values for groups are interpreted as their external ID and structure levels as their name within that meeting.
- If no group exists for a meeting and no default is given, the meetings default group is used. (Logged as warning)
- If a structure level does not exist, it is created.
- Vote weights need to be given as 6 digit decimal strings.

```js
"meeting_mappers": [{
   "name": "Mapper-Name",
   "external_id": "M2025",
   "allow_update": "false",
   "conditions": [{
       "attribute": "membernumber", 
       "condition": "1426\d{4,6}$" 
   }, { 
       "attribute": "function",
       "condition": "board"
   }],
   "mappings": {    
       "groups": [{
           "attribute": "membership",
           "default": "admin, standard"
       }],
       "structure_levels": [{
           "attribute": "ovname",
           "default": "struct1, struct2"
       }],
       "number": {"attribute": "p_number"},
       "comment": {
           "attribute": "idp_comment",
           "default": "Group set via SSO"
        },
       "vote_weight": {
           "attribute": "vote",
           "default":"1.000000"
       },
       "present": {
           "attribute": "present_key",
           "default":"True"
       }
   }
}]
```
If you are using Keycloak as your SAML-server, make sure to fill the attributes of all users. Then you also need to configure for each attribute in 'Clients' a mapping for your Openslides services 'Client Scopes'. Choose 'User Attribute' and assign the 'User Attribute' as in the step before and the 'SAML Attribut Name' as defined in Openslides 'meeting_mappers'.

## Return Value

The action always returns the `user_id` in the response object in `response.json["results"][0][0]['user_id']`

## Permissions
This action can be called only from inside the stack. This will be done from the auth service on login of a user for OpenSlides. There are no more permissions required.
