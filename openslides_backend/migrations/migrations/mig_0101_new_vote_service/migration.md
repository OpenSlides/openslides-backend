# Short overview

Current split between automatic and manual actions:

* Simple changes like adding, editing and removing collection, field or most of
  the field attributes are being handled by the diff generator (usually) almost
  fully automatically. Developer needs to run the script, check the output and
  adjust the diff only in rare cases.

* Renames are being handled semi-automatically: developer needs to define the
  renames dictionary in the Migration class.

* Special almost automatic handling of (currently) 3 specific cases:
  * A new required field in existing collection:
    * creating a required field
    * adding `required: true` to an existing field
  * Field rename that results in writing side switch (table field becomes view
    field or other way around)
  * Field getting a new/more strict enum type:
    * change from string/string[] to enum/enum[]
    * Removing option from an existing enum

  Diff generator collects such cases, generates the maps that should be used
  to finish handling such cases in the cleanup method of te migration class and
  writes them to the `DiffMixin` class defined in the new file next to the
  `migration.py`.
  Developer has to import and extend it `DiffMixin` in the migration class.
  `BaseMigration` class will handle the fields from `DiffMixin`.

  **Note:** side switch is not relevant for the vote
  service, therefore will be implemented later.

* Complex logic like moving data between columns and tables, creating or
  updating entries, modifying data in renamed columns etc. should be defined
  by the developer, mainly in `data_manipulation` method of the migration class.
  Some actions are getting partially automated:
    * Saving the data for `data_manipulation` into the temporary tables. Developer has
      to define the collections and fields to save in `migration_tables`.
    * Helper methods will patially automate some common actions.

# Dammi changes needed for this migration

* Diff generator:
  * renamed fields should not be completely skipped in diff generator as we
    may need to update to/reference. Example in new vote service:
    * projector/used_as_default_projector_for_poll_in_meeting_id -> projector/used_as_default_projector_for_topic_poll_in_meeting_id
    * meeting/default_projector_poll_ids -> meeting/default_projector_topic_poll_ids
  * Data has to be generated and written to the `DiffMixin` for 3 cases described above.

# Will be needed soon

For Zitadel (and maybe motion/diff_version):
* When field with `required: true` gets created or this attribute gets added
  to the field:
  * If `default` is set for the field, also update all the existing entries
    with `UPDATE table_name SET column_name = value WHERE TRUE;`. This can
    happen in diff generator.
  * Allow developer to define default for this migration instead of using
    default from the collection file.

# Not relevant for vote service migration but let's keep it somewhere for now

* Relation side switch:
  * Technically can happen on rename of 1-1 relational fields.
  * At some point we may also want to manually switch the writing side of some
    relations to make it more logical.
  * For now Hannes will implement a simple assertion that will raise error in such cases.
  * The intended way to handle side switch detected by diff generator:
    * Diff generator collects these cases and adds `switched_writing_side` to
      the `DiffMixin`.
    * In the migration class the previous writing side must be automativally
      saved in migration table in `data_preparation`
    * In `data_manipulation` data from the migration table gets automatically
      transfered into the new table field

# Base class

## data_manipulation

General pattern:

* Handle data from the copied tables
* For reserve_ids use MigrationHandler.update_sequences()
* needs helper to retrieve data from the migration table. Catch errors for non existent tables/columns and raise error with add to map suggestion.

### Common actions

* Needed for vote service:
  * transform(collection, field, transform_func, *args, **kwargs)
  * transform_and_rename(collection, old_field, new_field, transform_func, *args, **kwargs)
* Could be needed in the future:
  * move(old_collection, old_field, new_collection, new_field)
  * transform_and_move(old_collection, old_field, new_collection, new_field, transform_func, *args, **kwargs)

# data_preparation

* poll_candidate
* poll_candidate_list
* option
* user
* meeting
* meeting_user
* nm_group_meeting_user_ids_meeting_user_t
* ...

# data_manipulation

## transform_and_rename

* poll/type -> poll/visibility and the values have changed:
  * analog -> manually
  * named -> open
  * pseudoanonymous -> secret
  * cryptographic There should be no case. If so, "secret" can be used.
* meeting/poll_default_method -> meeting/topic_poll_default_method: always selection (introduce and use here the default functionality?)

### replace_value_from_map

* Group/permissions: poll.can_manage -> agenda_item.can_manage_polls

## Complex manipulation

### mu

* meeting_user/vote_delegated_to_id -> meeting_user/vote_delegated_to_ids:
  * Type changes from relation to relation-list. In backend vote_delegated_to_ids remains the writing side.
  * Value should be transformed as: value -> list with this value as a single item

### poll_config_X

* Fields were moved to poll_config_X collections, data has to be migrated.
  Refer to [Migrating the polls](#migrating-the-polls) for more details:
  * poll/pollmethod
  * poll/min_votes_amount
  * poll/max_votes_amount
  * poll/max_votes_per_option
  * poll/option_ids
* poll/onehundred_percent_base -> poll_config_X/onehundred_percent_base and
  some values have changed:
  * YN -> yes_no
  * YNA -> valid
  * Y -> no_general
  * N -> no_general (+ poll_config_selection/strike_out: true)
  * valid: no changes.
  * cast: no changes.
  * entitled: no changes.
  * entitled_present: no changes.
  * disabled: no changes.

### meeting_poll_default

* (move) meeting/*_poll_default_group_ids -> meeting_poll_default/group_ids
* (move) meeting/*_poll_sort_poll_result_by_votes -> meeting_poll_default/sort_result_by_votes. NOTE: poll_default_type -> topic_, motion does not exist
* (move and transform)(like poll/type) meeting/*_poll_default_type -> meeting_poll_default/visibility. NOTE: poll_default_type -> topic_
* (move and transform)(like poll/onehundred_percent_base) meeting/*_poll_default_onehundred_percent_base -> meeting_poll_default/onehundred_percent_base. NOTE: poll_default_onehundred_percent_base -> topic_
* For topic polls: meeting_poll_default/display_chart: pie
* For assignment polls, meeting/assignment_poll_default_method:
  * Y
    * meeting_poll_default/method -> selection
  * N
    * meeting_poll_default/method -> selection
    * meeting_poll_default/strike_out -> true
  * YN
    * meeting_poll_default/method -> rating_approval
  * YNA
    * meeting_poll_default/method -> rating_approval
    * meeting_poll_default/allow_abstain -> true

### Poll

* poll/state: The value `published` was removed. Published polls have to be migrated:
  * poll/state -> `finished`.
  * poll/published -> `true`.

### Poll/result

* Fields were removed, `poll/result` has to be generated from them. Refer to
  [Migrating the polls](#migrating-the-polls) for more details:
  * poll/global_yes
  * poll/global_no
  * poll/global_abstain
  * poll/global_option_id
  * poll/votescast
  * poll/votesinvalid

### Ballots and options

Look below.

# --- Copied from vote-service/Migration.md ---

### General rules

The following information is relevant for all the poll types.

#### poll, poll_config_X, poll_entitled_user and poll_option

Regardless of the type, for each old poll 2 models have to be created: a new
`poll` and a related `poll_config_X`. If `entitled_users_at_stop` are written for the poll, its content has to be transformed into entries of `poll_entitled_user`. Additionally for some poll types
`poll_option` models should be generated.

`entitled_users_at_stop` should be processed the same way for all the
polls. For each item in `entitled_users_at_stop` an entry of
`poll_entitled_user` has to be created:

```
{
  poll_id: new_poll.id,
  meeting_user_id (optional, if user is in the meeting): meeting_user_id from old_item.user_id and poll.meeting,
}
```

How the data should be migrated depends on whether it is a motion, assignment
or a topic poll. When it comes to assignement polls, there are 3 possibilities
based on content_object_id and whether the global yes or no option is used.

#### poll_ballot objects and poll/result

If old_poll.type is "analog" (corresponds to the new visibility "manually"),
no ballots should be created for the poll. Othervise `poll_ballot` models
should be generated from the old votes.

If poll.state is "created" or "started", then poll/result is empty. Otherwise
it should be generated from the old votes and options.

Additionally to the calculated part, poll/result can include 2 extra values
carried over from the old poll:

* total_ballots (old_poll.votescast): it's the total number of votes that
  includes both valid and invalid votes. Should be always included into the
  result.
* invalid (old_poll.votesinvalid): should be included into the result only if
  new_poll.visibility == "manually"

"total_ballots" and "invalid" should be saved as integers.

Old polls used to have a separate field for the valid votes: `votesvalid`. It
should be omitted in the migration.

For each poll that is not anonymized, per each `poll_ballot` an additional
`poll_ballot_user` instance should be created:

```
{
  poll_id: poll_ballot.poll_id,
  poll_ballot_id: poll_ballot.id,
  acting_meeting_user_id (optional, if user is in the meeting): meeting_user_id from old_vote.delegated_user_id and poll.meeting,
  represented_meeting_user_id (optional, if user is in the meeting): meeting_user_id from old_vote.user_id and poll.meeting
}
```

### motion

#### poll_config_approval

```
{
  poll_id: new_poll.id,
  allow_abstain: if old.method == "YNA" then "true" else "false",
  onehundred_percent_base: old_poll.onehundred_percent_base. Map (old_poll -> new):
      - YN -> yes_no
      - YNA -> valid
      - valid: (remains unchanged).
      - cast: (remains unchanged).
      - entitled: (remains unchanged).
      - entitled_present: (remains unchanged).
      - disabled: (remains unchanged).
      - Y -> @panic(not allowed for this config type)
      - N -> @panic(not allowed for this config type)
}
```

#### poll

```
{
  title: old.title,
  visibility: old.type. Map (old -> new):
      - analog -> manually
      - named -> open
      - pseudoanonymous -> secret
      - cryptographic -> @panic(immpossible)
  state: if old.state == "published" then "finished" else old.state,
  result: see below,
  published: old.state == "published",
  anonymized: old.is_pseudoanonymized,
  allow_invalid: false,
  allow_vote_split: false,
  live_voting_enabled: old.live_voting_enabled,
  sequential_number: old.sequential_number,
  content_object_id: old.content_object_id,
  entitled_group_ids: old.entitled_group_ids,
  meeting_id: old.meeting_id,
}
```


#### poll/result

In the old system, there is one option per poll. There is also a global option,
but this can be ignored. The new `poll/result` essentially corresponds to this
single option. If there is more than one option, then @panic.

Values for "invalid" and "total_ballots" should be stored as integers. The
other values are strings as they are decimal.

Example: `{"yes":"32","no":"20","abstain":"10","invalid":2,"total_ballots":64}`

Calculated from `old_poll.option_ids[0].vote_ids`:

```
{
  yes: option.yes -> string,  (skip if 0)
  no: option.no -> string,  (skip if 0)
  abstain: option.abstain -> string,  (skip if 0)
  invalid: old_poll.votesinvalid if new_poll.visibility == "manually" -> number,  (skip if 0)
  total_ballots: count(option.vote_ids) -> number
}
```

#### poll_ballot

In the old system only one vote should exist per user. The votes can be found
via `old_poll.option_ids[0].vote_ids`. For each old vote a new
`poll_ballot` object sould be created:

```
{
  poll_id: new_poll.id,
  weight: old.weight,
  split: false,
  value: Map (old -> new):
      - Y -> yes
      - N -> no
      - A -> abstain
      - else @panic(impossible value)
  acting_meeting_user_id (optional, if user is in the meeting): meeting_user_id from old.delegated_user_id and poll.meeting,
  represented_meeting_user_id (optional, if user is in the meeting): meeting_user_id from old.user_id and poll.meeting
}
```


### assignment with poll_candidate_list

If in the old system the collection of `old_poll.content_object_id` is
`poll_candidate_list`, the following collections should be created the same way
as for the [Motion poll](#motion):

* poll_config_approval
* poll (including calculation of poll/result)
* poll_ballot

#### poll_option

Additionally, each `poll_candidate` ("old") in
`old_poll.option_ids[0].content_object_id.poll_candidate_ids` should be saved as
a `poll_option`:

```
{
  poll_id: new_poll.id,
  weight: old.weight,
  text: NULL,
  content_object_id: fqid from "user" and old.user_id
}
```

### topic

`poll` is being created the same way as for [Motion poll](#motion). The other
collections are being migrated differently.

#### poll_config_selection

```
{
  poll_id: new_poll.id,
  max_options_amount: old_poll.max_votes_amount,
  min_options_amount: old_poll.min_votes_amount,
  allow_nota: old_poll.global_option_id exists,
  strike_out: old_poll.pollmethod == N,
  display_chart: pie,
  onehundred_percent_base: no_general
}
```

#### poll_option

A new `poll_option` should be created for each old `option` ("old"). They can
be found via `old_poll.option_ids`.

```
{
  poll_id: new_poll.id,
  weight: old.weight,
  text: old.text,
  content_object_id: None
}
```

#### poll/result

For each old option there is one entry in the result dict. The key is the
poll_option.text. The value is being calculated from the old votes.

`global_yes` and `global_no` in polls with `poll_config_selection` are being
calculated separately into the value "nota".

Example: `{"Option 1":"40","Option 2":"23","nota":"6","abstain":"7","invalid":3,"total_ballots":79}`

Calculation:
```
{
  for each option (if not option.used_as_global_option_in_poll_id == old_poll.id):
    poll_option.text: option.yes -> string,  (skip if value is 0)

  abstain: sum(all_options.abstain) -> string,  (skip if 0)
  nota: old_poll.global_option_id -> (option.yes + option.no) -> string,  (skip if 0)
  invalid: old_poll.votesinvalid if new_poll.visibility == "manually" -> number,  (skip if 0)
  total_ballots: old_poll.votescast -> number
}
```

#### poll_ballot

```
{
  poll_id: new_poll.id,
  weight: old.weight,
  split: false,
  value: old.value -> Replace old options ids with corresponding new poll_options ids,
  acting_meeting_user_id (optional, if user is in the meeting): meeting_user_id from old.delegated_user_id and poll.meeting,
  represented_meeting_user_id (optional, if user is in the meeting): meeting_user_id from old.user_id and poll.meeting
}
```

### assignment with global_yes or global_no

Assignment polls with `global_yes` or `global_no` in the new voting system will
function almost like the topic polls: with `poll_config_selection` but with
`content_object_id`s instead of the `text` in `poll_option`.

Migrate poll this way if:

* Collection of the old poll's content_object_id is `assignment`
* Old poll has `global_option_id`
* `global_yes` and/or `global_no` for the poll is true

The following collections should be created the same way
as for the [Topic poll](#topic):

* poll
* poll_option
* poll_ballot

Other collection have minor differences.

#### poll_config_selection

`poll_config_selection` for the assignment poll is similar to the topic poll
but it always has `allow_nota: true` and should not have `display_chart`:

```
{
  poll_id: new_poll.id,
  max_options_amount: old_poll.max_votes_amount,
  min_options_amount: old_poll.min_votes_amount,
  allow_nota: true,
  strike_out: old_poll.pollmethod == N,
  display_chart: null,
  onehundred_percent_base: old_poll.onehundred_percent_base. Map (old_poll -> new):
      - YNA -> valid
      - Y -> no_general
      - N -> no_general
      - valid: (remains unchanged).
      - cast: (remains unchanged).
      - entitled: (remains unchanged).
      - entitled_present: (remains unchanged).
      - disabled: (remains unchanged).
      - YN -> @panic(not allowed for this config type)
}
```

#### poll/result

Calculated similarly to the topic polls, but ids of the poll_options created
above are used as the keys instead of the poll_option/text.

Example: `{"1":"40","2":"23","nota":"6","abstain":"7","invalid":3,"total_ballots":79}`

Calculation:
```
{
  for each option (if not option.used_as_global_option_in_poll_id == old_poll.id):
    poll_option.id: option.yes -> string,  (skip if value is 0)

  abstain: sum(all_options.abstain) -> string,  (skip if 0)
  nota: old_poll.global_option_id -> (option.yes + option.no) -> string,  (skip if 0)
  invalid: old_poll.votesinvalid if new_poll.visibility == "manually" -> number,  (skip if 0)
  total_ballots: old_poll.votescast -> number
}
```

### assignment: other cases

#### poll_config_rating_approval

```
{
  poll_id: new_poll.id,
  max_options_amount: old.max_votes_amount,
  min_options_amount: old.min_votes_amount,
  allow_abstain: if old.method == "YNA" then "true" else "false",
  onehundred_percent_base: old.onehundred_percent_base. Map (old -> new):
      - YN -> yes_no
      - YNA -> valid
      - valid: (remains unchanged).
      - cast: (remains unchanged).
      - entitled: (remains unchanged).
      - entitled_present: (remains unchanged).
      - disabled: (remains unchanged).
      - Y -> @panic(not allowed for this config type)
      - N -> @panic(not allowed for this config type)
}
```

#### poll

```
{
  title: old.title,
  visibility: old.type. Map (old -> new):
      - analog -> manually
      - named -> open
      - pseudoanonymous -> secret
      - cryptographic -> @panic(immpossible)
  state: if old.state == "published" then "finished" else old.state,
  result: see below,
  published: old.state == "published",
  anonymized: old.is_pseudoanonymized,
  allow_invalid: false,
  allow_vote_split: false,
  live_voting_enabled: old.live_voting_enabled,
  sequential_number: old.sequential_number,
  content_object_id: old.content_object_id,
  entitled_group_ids: old.entitled_group_ids,
  meeting_id: old.meeting_id
}
```

#### poll_option

For each old option ("old"), the option.content_object_id value has to be a
`user` collection. Otherwise, @panic. Old content_object_id gets directly
transfered to the poll_option/content_object_id field.

```
{
  poll_id: new_poll.id,
  weight: old.weight,
  text: NULL,
  content_object_id: old.content_object_id
}
```

#### poll/result

Poll/result is a dict. There is one entry for each old option. The key is
the poll_option-id created above. The values "yes", "no" and "abstain" are
adopted as objects.

Example: `{"1":{"yes":"5","no":"1"},"2":{"yes":"1","abstain":"6"},"invalid":1,"total_ballots":7}`

Calculation:
```
{
  for each option:
    option.id: {
      yes: option.yes -> string,  (skip if 0)
      no: option.no -> string,  (skip if 0)
      abstain: option.abstain -> string   (skip if 0)
    },

  invalid: old_poll.votesinvalid if new_poll.visibility == "manually" -> number,  (skip if 0)
  total_ballots: old_poll.votescast -> number
}
```

#### poll_ballot

In the old system for each pair user-option a sepatate `vote` was created. A single
`poll_ballot` should be generated for each group of the votes with the same
`user_token`. All of these votes must have the same `weight` - else @panic.

Old votes that can be found via `old_poll.option_ids.vote_ids`.

Calculation (one `poll_ballot` per each `user_token`):

```
{
  poll_id: new_poll.id,
  weight: old.weight (must be same for all),
  split: false,
  value: see below,
  acting_meeting_user_id (optional, if user is in the meeting): meeting_user_id from old.delegated_user_id and poll.meeting,
  represented_meeting_user_id (optional, if user is in the meeting): meeting_user_id from old.user_id and poll.meeting
}
```

Example of `poll_ballot.value`: `{"1":"yes","2":"abstain"}`.

It's a dictionary where each key-value pair represents an old `vote`:

* key: vote.option_id -> should be replaced with the id of the new `poll_option`
  instances created above
* value: transformed vote.value:
      - Y -> yes
      - N -> no
      - A -> abstain
      - else @panic(impossible value)


## Changes in old fields by collection

### Poll_candidate, option -> poll_option

* Parts `poll_candidate` and `option` were absorbed by the new collection `poll_option`:
  * poll_option/weight:
    * option/weight
    * poll_candidate/weight
  * poll_option/poll_id:
    * option/poll_id
    * poll_candidate_list_id.option_id.poll_id
  * poll_option/text:
    * option/text
    * None
  * poll_option/content_object_id:
    * if collection of content_object_id == "user" -> option/content_object_id
    * fqid from "user" and poll_candidate/user_id

### Option -> other collections

* The following fields were removed but have to be used in the migration for
  generating values for generating poll/result:
  * yes, no and abstain
  * vote_ids


### Vote -> poll_ballot

* The `vote` collection was renamed into `poll_ballot`.
* Field was removed. No migration necessary:
  * vote/meeting_id
* vote/user_token: is used to merge old votes into new ballots
* vote/option_id: replaced with the direct relation to the poll. Needs
  migration: vote.option_id/poll_id -> poll_ballot/poll_id.

### Vote -> poll_ballot_user

* vote/option_id: replaced with the direct relation to the poll. Needs
  migration: vote.option_id/poll_id -> poll_ballot_user/poll_id.
* vote/user_id -> poll_ballot_user/represented_meeting_user_id (only if user is
  in meeting, needs to be generated from user_id and meeting_id).
* vote/delegated_user_id -> poll_ballot_user/acting_meeting_user_id (only if
  user is in meeting, needs to be generated from user_id and meeting_id).
* poll_ballot_user/poll_ballot_id: id of the poll_ballot instance generated
  from the same vote.
