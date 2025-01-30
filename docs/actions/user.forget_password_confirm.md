## Payload

```js
{
  // Required fields
  new_password: String;
  user_id: Id;
  authorization_token: String;
}
```

## Action

This action confirms the changing of a user's password without being authenticated. After a user entered their email-address and clicked on the by an email received link, the user has to enter a new password.
This new password will be sent by this action to the backend. Besides, the client has to send an `authorization`-token. The token is read from a query-parameter given by the url (`?user_id=<user_id>&token=<token>`). The received token (given in the `authorization` header) is a jsonwebtoken. It is then verified that the token is valid (is has to be verified, that it is issued ten minutes or less ago and its signature is valid). If the token is valid, the token's payload contains `{ user_id: Id; email: String; }`. If then the `user_id` from the token's payload matches the received `user_id`, the user's (given by the `user_id`) password is set to the new password `new_password`.

## Permission

None, but action raises action error, if saml_id of user is set