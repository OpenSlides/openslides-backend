## Payload
```
{ id: Id; }
```

## Actions
`motion_category.number_motions` is called with the id of the _main category_ to number all motions. Categories itself build a tree with the `motion_category/parent_id`/`motion_category/children_ids` and `motion_category/weight` fields. We are going to number all motions in all *affected categories*. The set of affected categories includes the main category and all categories in the tree of categories below it. These motions are called _affected motions_, since they will all be renamed. All affected motions are numbered in the order of `motion/category_weight`.

First thing to do is a precheck regarding *amendments* (A motion which has a lead motion; relation `motion/lead_motion_id`). For each affected motion it is checked if it is an amendment and if so, that the lead motion is also an affected motion. If this is not true for each affected motion, an error must be returned. [This is the original error message](https://github.com/OpenSlides/OpenSlides/blob/stable/3.4.x/server/openslides/motions/numbering.py#L168).

Next, we need to handle motion category prefixes. The prefix is optional, so it can be empty. The prefix is going to be a part of the `motion/number`. We want to have the following: If a prefix of an affected category is empty, it should get the prefix from the parent. This stops when reaching the main category, e.g. if it has no prefix, each child that does not have prefixes will also not get a prefix (this is intended). Also the prefixes of the categories do not change, this is just for numbering. So it might be good to create a dictionary `prefixes`, which maps a calculated prefix to each category. E.g. if you have this (linear) tree (syntax: `<id>: <prefix>`): `1: "A"` -> `2: ""` -> `3: "B"`, this would be the mapping: `{1: "A", 2: "A", 3: "B"}`. Another example: `1: "A"` -> `2: ""` -> `3: "B"` where the main category is 2 (1 is not an affected category!), this would be the mapping: `{2: "", 3: "B"}`.

Now onto the new `number` values to generate. Remember that `motion/number` is a string. We have multiple counters for the actual numbervalue (the actual integer), named `number_value` (see similarities to [motion.create](motion.create.md)),  beginning at 1. For all non-amendments, there is one single counter, named _main counter_. There is also a counter for every amendment's lead motion, so the amendments of one lead motion can be numbered. For every affected motion, do:

- If the motion is not an amendment, the `number` consists of three parts `ABC`:
  - `A`: the prefix form `prefixes` of the category of the motion
  - `B`: `" "` if `meeting/motions_number_with_blank` is set, else `""`
  - `C`: Take the value of the main counter. Fill it with leading zeros until the `meeting/motions_number_min_digits` number of digits is reached. Increase the counter.
- If the motion is an amendment, the `number` consists of five parts `ABCDE`:
  - `A`: The lead motions **new** number
  - `B`: `" "` if `meeting/motions_number_with_blank` is set, else `""`
  - `C`: The value of `meeting/motions_amendments_prefix`
  - `D`: `" "` if `meeting/motions_number_with_blank` is set, else `""`
  - `E`: Take the value of the counter for the lead motion of the motion. Fill it with leading zeros until the `meeting/motions_number_min_digits` number of digits is reached. Increase the counter.

Check new numbers: if there is a non-affected motion in the meeting which has one of the fresh calculated numbers, [return a nice error](https://github.com/OpenSlides/OpenSlides/blob/stable/3.4.x/server/openslides/motions/numbering.py#L230). This ensures that all numbers are unique.

At last, set all new numbers.

### One rather complete example
Category tree (Syntax: `(<prefix>) <Name> <ID>`, empty parenthesis, if the category does not have a prefix):
```
(A) Allgemein 1
|-(B) Bildung 2
    |-() Sonstiges 3
    |   |-(K) Unter-Sonstiges 4 
    |-(S) Schule 5
```
Motions sorted into the category tree (`category_id` and `category_weight` are implicitly given by the tree). The names are just their DB ids. All motions do not have numbers yet. In parenthesis additional infomation is given for the motion
```
(A) Allgemein 1
|- 1
|- 2
|-(B) Bildung 2
    |-3 (lead_motion_id=7)
    |-4
    |-() Sonstiges 3
    |   |-5
    |   |-6
    |   |-(K) Unter-Sonstiges 4 
    |      |-7
    |      |-8
    |-(S) Schule 5
    |-9
    |-10
```

Now, we are numbering `(B) Bildung 2`. Settings:
`meeting/1/motions_number_with_blank=true`, `meeting/1/motions_number_min_digits=3`, `meeting/1/motions_amendments_prefix="X-"`. This is the result:
```
(A) Allgemein 1
|- 1
|- 2
|-(B) Bildung 2
    |-3 "K 004 X- 001"
    |-4 "B 001"
    |-() Sonstiges 3
    |   |-5 "B 002"
    |   |-6 "B 003"
    |   |-(K) Unter-Sonstiges 4 
    |      |-7 "K 004"
    |      |-8 "K 005"
    |-(S) Schule 5
    |-9 "S 006"
    |-10 "S 007"
```

#### Failure case 1
Numbering `(B) Bildung 2` does not work:
```
(A) Allgemein 1
|- 1
|- 2
|-(B) Bildung 2
    |-3 (lead_motion_id=1) <-- Changed lead motion
    |-4
    |-() Sonstiges 3
    |   |-5
    |   |-6
    |   |-(K) Unter-Sonstiges 4 
    |      |-7
    |      |-8
    |-(S) Schule 5
    |-9
    |-10
```
The error should be something like `Amendment "3" cannot be numbered, because it's lead motion (1) is not in category B - Bildung or any subcategory.`

#### Failure case 2
```
(A) Allgemein 1
|- 1 with number "B 002" <-- Changed
|- 2
|-(B) Bildung 2
    |-3 (lead_motion_id=7)
    |-4
    |-() Sonstiges 3
    |   |-5
    |   |-6
    |   |-(K) Unter-Sonstiges 4 
    |      |-7
    |      |-8
    |-(S) Schule 5
    |-9
    |-10
```
Should fail with an error like: `Numbering aborted because the motion identifier "B 002" already exists in category A - Allgemein.`

## Permissions
The request user needs `motion.can_manage`.
