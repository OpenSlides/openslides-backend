## Payload
```
{
// Required
    id: Id;
    
// Optional
// Group A
    name: string;
    description: HTMLStrict;
    legal_notice: string;
    privacy_policy: string;
    login_text: string;
    theme_id: Id;
    default_language: string;
    users_email_sender: string;
    users_email_replyto: string;
    users_email_subject: string;
    users_email_body: text;
    require_duplicate_from: boolean;
    
// Group B
    enable_electronic_voting: boolean;
    enable_chat: boolean;
    enable_anonymous: boolean;
    reset_password_verbose_errors: boolean;
    limit_of_meetings: int;
    saml_enabled: boolean;
    saml_login_button_text: string;
    saml_attr_mapping: JSON;
    saml_metadata_idp: text;
    saml_metadata_sp: text;
    saml_private_key: text;
}
```

## Action
Updates the organization.
It has to be checked that the theme_id has to be one of the theme_ids.
This is an example of the saml_attr_mapping, where you can see the mappable fields.
```js
{
   "email": "email",
   "title": "title",
   "gender": "gender",
   "pronoun": "pronoun",
   "saml_id": "username",
   "is_active": "is_active",
   "last_name": "lastName",
   "first_name": "firstName",
   "member_number": "member_number",
   "meeting_mappers": [
      {
         "name": "A mapper",
         "mappings": {
            "groups": [
               {
                  "default": "not_a_group",
                  "attribute": "idp_group_attribute"
               },
               {
                  "default": "not_a_group",
                  "attribute": "group_2"
               }
            ],
            "number": {
               "attribute": "participant_number"
            },
            "comment": {
               "default": "Vote weight, groups and structure levels set via SSO.",
               "attribute": "idp_commentary"
            },
            "present": {
               "default": "True",
               "attribute": "presence"
            },
            "vote_weight": {
               "default": "1.000000",
               "attribute": "vw"
            },
            "structure_levels": [
               {
                  "default": "structure1",
                  "attribute": "structure"
               }
            ]
         },
         "conditions": [
            {
               "attribute": "member_number",
               "condition": "LV_.*"
            },
            {
               "attribute": "email",
               "condition": "[\\w\\.]+@([\\w-]+\\.)+[\\w]{2,4}"
            }
         ],
         "external_id": "Bundestag"
      },
      {
         "name": "Bundestag visitors",
         "conditions": [
            {
               "attribute": "member_number",
               "condition": "^(?!11600).*"
            }
         ],
         "external_id": "Bundestag"
      },
      {
         "name": "A second mapper",
         "mappings": {
            "number": {
               "attribute": "participant_number"
            },
            "comment": {
               "default": "This mapper adds everyone to the Landtag default group.",
            },
            "present": {
               "default": "True",
               "attribute": "presence"
            },
         },
         "external_id": "Landtag"
      }
   ],
   "is_physical_person": "is_person"
}
```

## Permissions
- Users with OML of `can_manage_organization` can modify group A
- Users with OML of `superadmin` can modify group B
