## Payload

```js
{
  // Required
  email: string;
}
```

## Action 

A user can change their password by this action without being authenticated. To perform a changing of their password the user enters their email-address (case insensitive). The client then sends a hard-coded reset email to the given email-address (as `email`). TODO: translations

Regardless if the email-address is used by a user, the client shows the user a successful message (for example "An email was successfully sent to the given email-address"). This is necessary to avoid filtering which email-address is used by an OpenSlides-user.

In the case that an email-address is used by a user, an email is sent to that email-address of that user including a link to set a new password. If multiple users use the same email address (case insensitive), one email is sent per user (case-sensitive).
The link redirects a user to `<domain>/login/forget-password-confirm?user_id=<user_id>&token=<token>`. 
As you can see, the user_id of the user and a token are given as query-parameters. The token is a [jsonwebtoken](https://jwt.io/) (specified by [RFC7519](https://datatracker.ietf.org/doc/html/rfc7519)), which is self-contained and up to ten minutes valid. The user_id and the email-address (as `email`) are given as payload to the token. Furthermore, the token is signed. The secret to sign the token is the secret which is used to sign `access_token`s. The algorithm `HS256` will be used. The token is given as a base64-encoded string.

To confirm the changing of the password, the action [user.forget_password_confirm](user.forget_password_confirm.md) has to be performed.

## Email text:

```text
You receive this email, because you have requested a new password for your OpenSlides-account.

Please open the following link and choose a new password:
<link>

For completeness your username: <username>
```

## Permission

None, but action raises action error, if idp_id of user is set