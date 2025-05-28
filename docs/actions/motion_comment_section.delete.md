## Payload
```js
{ id: Id; }
```


## Action
Deletes the comment section. It must fail, if there are still comments in this section. A nice error message informing which motions still have comments is needed.

## Permissions
The request user needs `motion.can_manage`.
