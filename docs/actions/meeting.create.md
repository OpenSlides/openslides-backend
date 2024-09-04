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
    url_name: string;
    organization_tag_ids: Id[];
    user_ids: Id[];
    admin_ids: Id[];
    set_as_template: boolean;
    external_id: string;
}
```

## Action
It has to be checked whether the `organization.limit_of_meetings` is unlimited (=0) or lower than the amount of active meetings in `organization.active_meeting_ids`.
 
When creating a meeting the following objects have to be created, too:
- Groups: `Default`, `Admin`, `Delegates`, `Staff`, `Committees`. The first one is set as `meeting/default_group_id`, the second one as `meeting/admin_group_id`. The permissions can be found in the [initial-data.json](https://github.com/OpenSlides/openslides-backend/tree/main/global/data/initial-data.json)).
- Projector: One projector named `"Default projector"` must be created and set as `meeting/reference_projector_id`.
- All default projectors (`meeting/default_projector_*_ids`, see `models.yml`) must be set to the one projector
- Motion workflow and states: Create one workflow `"simple workflow"` which is set as `meeting/motions_default_workflow_id`, `meeting/motions_default_amendment_workflow_id` and `meeting/motions_default_statute_amendment_workflow_id`. Create four states (analog as in the [initial-data.json](https://github.com/OpenSlides/openslides-backend/tree/main/global/data/initial-data.json)).
- Two countdowns are created and set as `meeting/list_of_speakers_countdown` (name: "List of speakers countdown") and `meeting/voting_countdown` (name: "Voting countdown").

If `user_ids` are given, it must be checked that it is a subset of `committee/user_ids`. Each user is added to the meeting by being added to the default group.

If `admin_ids` are given, it must be checked that it is a subset of `committee/user_ids`. Each user is added to the meeting by being added to the admin group.

The field `is_active_in_organization_id` has to be set to the organization_id.

If a meeting is created, `motion_poll_default_type` should be `pseudoanonymous` and `motion_poll_default_method` should be `YNA`.
If a meeting is created, `assignment_poll_default_type` should be `pseudoanonymous` and `assignment_poll_default_method` should be `Y`.
If a meeting is created, `assignment_poll_default_group_ids`, `motion_poll_default_group_ids` and `topic_poll_default_group_ids` should have the Delegates group.

If `set_as_template` is given, `template_for_organization_id` has to be set to `1`.

It translates created objects (eg. groups, workflow, states, ...) to the given language `language`. 

## Permissions
The user must have CML `can_manage`.
If the organization setting: `require_duplicate_from` is set, OML rights are required.
