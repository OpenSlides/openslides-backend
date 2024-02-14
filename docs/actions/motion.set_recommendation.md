## Payload
```
{
    id: Id;
    recommendation_id: Id;
}
```

## Action
The `recommendation_id` must be state with a recommendation label in the motions workflow. See [[https://github.com/OpenSlides/OpenSlides/wiki/Motions#motion-recommendation]].

## Permissions
The request user needs `motion.can_manage_metadata`.
