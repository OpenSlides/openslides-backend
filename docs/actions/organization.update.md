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
    gender_ids: Id[];
    
// Group B
    enable_electronic_voting: boolean;
    reset_password_verbose_errors: boolean;
    limit_of_meetings: int;
    enable_chat: boolean;
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

Checks for deleted genders and clean the gender of users which have deleted genders.

## Permissions
- Users with OML of `can_manage_organization` can modify group A
- Users with OML of `superadmin` can modify group B
