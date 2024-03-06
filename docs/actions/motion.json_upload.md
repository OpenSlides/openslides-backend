## Payload

Because the data fields are all converted from CSV import file, **they are all of type `string`**. 
The types noted below are the internal types after conversion in the backend. See [here](preface_special_imports.md#internal-types) for the representation of the types.
```js
{
    // required for new motions
    data: {
        // required in create
        title: string,             // info: done, error
        text: string,              // info: done, error
        // all optional, but see rules below
        number: string,            // unique when set, info: done, generated or error
        reason: string,            // required for create if the meeting has "motions_reason_required", info: done or error
        submitters_verbose: string[],      
        submitters_username: string[], // info: done, generated, warning, error if len(submitters_verbose) > len(submitters_username) 
        supporters_verbose: string[],
        supporters_username: string[], // info: done, warning, error if len(supporters_verbose) > len(supporters_username)
        category_name: string,     // info: done or warning, partial reference to: motion_category
        category_prefix: string,
        tags: string[],            // info: done or warning, reference to: tag
        block: string,             // info: done or warning, reference to: motion_block
        motion_amendment: boolean,    // info: done or warning, if True, warning, that motion amendments cannot be imported
    }[];
    meeting_id: Id, // id of the current meeting.
}
```
## Return value and object fields

Besides the usual headers as seen in payload (name and type), there are these differences:

- `submitters`, `supporter_users`, `category_name/prefix`, `tags` and `block`: Objects that show if the model has been found (`done`) or not (`warning`).
- `text`: will be surrounded in html `<p></p>` tags if the string isn't encased in html tags already.
- `number`: will be object with error, if the field is set and another row in the payload has the same number. If the `number` field is left empty and the motion is going to be created in a `motion_state` where `set_number` is true, a new `number` will be generated and the object is going to have the info `generated`.

The row state can be one of "new", "done" or "error". In case of an error, no import should be possible.

See [common description](preface_special_imports.md#general-format-of-the-result-send-to-the-client-for-preview).

Other than the validity check for the username-fields, `submitters_verbose` and `supporters_verbose` are NOT otherwise used or taken note of in the import. They are merely accepted in order to check that someone didn't accidentally edit the wrong column in a file that has both verbose and non-verbose columns.
They are not included in the return value.


## Action
The data will create or update motions.

### Motion matching

Motions can be updated via their `number`.
If a motion has a `number`, it will be matched with and updated with the data of any import date that has the same `number`.
Therefore motions that don't have a number can not be overwritten.

## Permission
Permission `motion.can_manage`