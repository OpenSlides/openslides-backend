# Payload

```js
{
    mediafile_ids: Id[];
}
```

## Returns

```js
{
  [mediafile_id: Id]: {
    owner_id: Fqid,
    published: boolean,
    meetings_of_interest: {
      [meeting_id: Id]: {
        name: string;
        holds_attachments: boolean;
        holds_logos: boolean;
        holds_fonts: boolean;
        holds_current_projections: boolean;
        holds_history_projections: boolean;
        holds_preview_projections: boolean;
      }
    },
    children_amount: int,
  }
}
```

## Logic

It iterates over the given `mediafile_ids`. For every id of `mediafile_ids` all objects are searched which are associated with that id. This means that for every meeting if the mediafile or one of its children is used as an attachment or as a logo/font.
The result is a dictionary whose keys are the `mediafile_ids`. The values are as follows: `owner_id` contains the fqid of the mediafiles owner, published will be true for orga mediafiles that are in the `meeting/published_mediafile_ids` list, `children_amount` is the amount of children the mediafile has (children of children included). The `meetings_of_interest` array contains the data for all the meetings where the mediafile or its children have attachments, logos, fonts or projections set.

## Permissions

The intended usage of this presenter is the preview on deletion or unpublishing of mediafiles on the orga level. Therefore the permissions are identical to that of the action [mediafile.delete](../actions/mediafile.delete.md)