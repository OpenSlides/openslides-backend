## Payload
```js
{
  // Required
  id: Id;
  
  // Optional
  meeting_id: Id;
}
```

## Action
For each PayloadElement there can be multiple ActionData-items and there could be several PayloadElements.
Therefore, the action results usually with success = True, except there is an unexpected error. You have to check the individual results in the 2 dimensional (payloadElement/ActionData) array for a `send = true` or `false`. In case of `false` you'll get an error message, too.
If possible, all result items contain the `recipient_user_id` and `recipient_meeting_id`. 
For details of results have a look at the tests [here](https://github.com/OpenSlides/openslides-backend/blob/main/tests/system/action/user/test_send_invitation_email.py).

It must be checked, that a user (given by the key `id`) belongs to a meeting (given by the key `meeting_id`). If not, `send` is set to `False` and an explicit message is included. Also, the user must have `user/email` set. If it is empty or invalid, there will be an appropiate message.

Check the `meeting/users_email_sender` (if a meeting is given by `meeting_id`) or the `organization/users_email_sender` (senders name): If one of the characters `[`, `]` or `\` is in the string, you'll get an error message in the result.  (See [here for OS3-Code](https://github.com/OpenSlides/OpenSlides/blob/7315626e18c0515b6ff61551c705156cbd5056cb/server/openslides/users/models.py#L275))

Send an email to a user with
- The `to` header set to the users email address
- The `from` header:
  if given, use `meeting/users_email_sender` as senders name together with `DEFAULT_FROM_EMAIL` read from the environment variables as eMail address..
- The `Reply-To` header: `meeting/users_email_replyto` if it is not empty
- `subject` and `body`: see below.

[This is the OS3 code](https://github.com/OpenSlides/OpenSlides/blob/7315626e18c0515b6ff61551c705156cbd5056cb/server/openslides/users/models.py#L236). [And this one](https://github.com/OpenSlides/OpenSlides/blob/70d5b32bd7c65d75c024fd2162516ed94ec9c080/server/openslides/users/views.py#L520). Please have a look at it due to excessive error handling.

If the email could be send successfully you get a response for the corresponding ActionData-item with `{"send": true}` otherwise with `{"send": false}`.

### Subject
Use `meeting/users_email_subject` (if a meeting is given by `meeting_id`); otherwise use `organization/users_email_subject`. The string can have placeholders like `{username}` in it. Provide
- `event_name` as `meeting/name` (if a meeting is given, otherwise `organization/name`) and
- `username` as `user/username`
- `name` as the users short name
- `title` as `user/title`
- `given_name` as `user/first_name`
- `surname` as `user/last_name`
- `groups` as a listing of the names of the users groups in the meeting
- `structure_levels` as a listing of the names of the users structure_levels in the meeting
to be replaced in the template (see [here](https://github.com/OpenSlides/OpenSlides/blob/7315626e18c0515b6ff61551c705156cbd5056cb/server/openslides/users/models.py#L266))

### Body
It does an equal string formatting  as for the subject. Use `meeting/users_email_body` (if a meeting is given by `meeting_id`, otherwise it's `organization/users_email_body`) and provide
- `event_name` as `meeting/name` (if a meeting is given, otherwise `organization/name`)
- `name` as the users short name
- `url` as `meeting/users_pdf_url` (this can only be used, if a meeting is given; otherwise it's the `organization/url`)
- `username` as `user/username` 
- `password` as `user/default_password`
- `title` as `user/title`
- `first_name` as `user/first_name`
- `last_name` as `user/last_name`
- `groups` as a listing of the names of the users groups in the meeting.
- `structure_levels` as a listing of the names of the users structure_levels.

### Unknown keywords in Subject or Body
Sending email is no longer refused, the wrong keyword will be injected instead.

## Permissions
The requesting user needs the permission `user.can_update` if a `meeting_id` is given or, if not, the permission OML `can_manage_users`.
