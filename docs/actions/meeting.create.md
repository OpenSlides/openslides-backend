## Payload
```js
{
// Required
    committee_id: committee/meeting_ids;
    name: string;
    language: string;

// Optional
    description: string;
    location: string;
    start_time: datetime;
    end_time: datetime;
    organization_tag_ids: Id[];
    user_ids: Id[];
    admin_ids: Id[];
    set_as_template: boolean;
    external_id: string; // unique in org
}
```

## Action
Creates a meeting.

Checks whether the `organization.limit_of_meetings` is unlimited (=0) or lower than the amount of active meetings in `organization.active_meeting_ids`.
 
The following objects are created, too:
- Groups: `Default`, `Admin`, `Delegates`, `Staff`, `Committees`. The first one is set as `meeting/default_group_id`, the second one as `meeting/admin_group_id`. The permissions can be found in the [initial-data.json](https://github.com/OpenSlides/openslides-backend/tree/main/data/initial-data.json)).
- Projector: One projector named `"Default projector"` is created and set as `meeting/reference_projector_id`.
- All default projectors (`meeting/default_projector_*_ids`, see `models.yml`) are set to that one projector
- Motion workflow and states: Creates one workflow `"simple workflow"` which is set as `meeting/motions_default_workflow_id` and `meeting/motions_default_amendment_workflow_id`. Creates four states (analog as in the [initial-data.json](https://github.com/OpenSlides/openslides-backend/tree/main/data/initial-data.json)).
- Two countdowns are created and set as `meeting/list_of_speakers_countdown` (name: "List of speakers countdown") and `meeting/voting_countdown` (name: "Voting countdown").

If `user_ids` are given, it checks if it is a subset of `committee/user_ids`. Each user is added to the meeting by being added to the default group.

If `admin_ids` are given, it checks if they are a subset of `committee/user_ids`. Each user is added to the meeting by being added to the admin group.
If they aren't given and `set_as_template` is not true, there will be an error.

The field `is_active_in_organization_id` is set to the organization_id.

If a meeting is created, 
* `motion_poll_default_type` is `pseudoanonymous`
* `motion_poll_default_method` is `YNA`
* `assignment_poll_default_type` is `pseudoanonymous`
* `assignment_poll_default_method` is `Y` 
* `assignment_poll_default_group_ids`, `motion_poll_default_group_ids` and `topic_poll_default_group_ids` have the Delegates group.

If `set_as_template` is given, `template_for_organization_id` is set to `1`.

Created objects (eg. groups, workflow, states, ...) are translated to the given language `language`. 

## Permissions
The user must have CML `can_manage`.
If the organization setting: `require_duplicate_from` is set, OML rights are required.
