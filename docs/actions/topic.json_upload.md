## Payload

Because the data fields are all converted from CSV import file, **they are all of type `string`**. 
The types noted below are the internal types after conversion in the backend. See [here](preface_special_imports.md#internal-types) for the representation of the types.
```
{
// required
    data: {
        // required
        title: string,
        // optional
        text: string,
        agenda_comment: string,
        agenda_duration: integer, // in minutes
        agenda_type: string,
    }[],
    meeting_id: Id, // id of the current meeting.
}
```
## Returns

Nothing special for this json_upload, see [common description](preface_special_imports.md#general-format-of-the-result-send-to-the-client-for-preview).

## Action
The data, which is enriched with the `meeting_id`, is saved in an action_worker. The action_worker, id and the preview data are returned. For generating the preview data it is looked for errors or duplicates.

## Permission
Need `agenda_item.can_manage` in this meeting.