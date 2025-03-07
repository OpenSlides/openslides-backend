## Payload:

```js
{
  // Required
  name: string;
  meeting_id: Id;

  // Optional
  first_state_name: string;
  states: [{
    // Required
    name: string;

    // Optional
    recommendation_label: string;
    css_class: string;
    restrictions: string[];
    allow_support: boolean;
    allow_submitter_edit: boolean;
    allow_create_poll: boolean;
    set_number: boolean;
    show_state_extension_field: boolean;
    show_recommendation_extension_field: boolean;
    merge_amendment_into_final: string;
    next_state_names: string[];
    previous_state_names: string[];
    weight: number;
    set_workflow_timestamp: boolean;
    allow_motion_forwarding: boolean;
  }]
}
```

## Action

This action creates a new `MotionWorkflow` with the given name in a meeting specified by the `meeting_id`. It also takes the optional array of states and creates a new `MotionState` with the given parameter (at least the name of a state) for every state. It then links the created states to the previously created workflow. The first state for the workflow is defined by the `first_state_name`, if specified, otherwise it is the first state in the array (if not empty).

A previous or next state is found by its name. A state can give an array of strings to define possible next or previous states. If a string matches the name of another state in the same array, then this state is one of the next or previous states (respectively).

The names of the states must be unique. Otherwise, this action raises an error.

## Permissions

A user needs the permission `motion.can_manage`.