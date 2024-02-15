## Payload


```js
{
  // Required
  id: Id;

  // Optional
  name?: string;
  primary_50?: HTMLColor;
  primary_100?: HTMLColor;
  primary_200?: HTMLColor;
  primary_300?: HTMLColor;
  primary_400?: HTMLColor;
  primary_500?: HTMLColor;
  primary_600?: HTMLColor;
  primary_700?: HTMLColor;
  primary_800?: HTMLColor;
  primary_900?: HTMLColor;
  primary_A100?: HTMLColor;
  primary_A200?: HTMLColor;
  primary_A400?: HTMLColor;
  primary_A700?: HTMLColor;
  accent_50?: HTMLColor;
  accent_100?: HTMLColor;
  accent_200?: HTMLColor;
  accent_300?: HTMLColor;
  accent_400?: HTMLColor;
  accent_500?: HTMLColor;
  accent_600?: HTMLColor;
  accent_700?: HTMLColor;
  accent_800?: HTMLColor;
  accent_900?: HTMLColor;
  accent_A100?: HTMLColor;
  accent_A200?: HTMLColor;
  accent_A400?: HTMLColor;
  accent_A700?: HTMLColor;
  warn_50?: HTMLColor;
  warn_100?: HTMLColor;
  warn_200?: HTMLColor;
  warn_300?: HTMLColor;
  warn_400?: HTMLColor;
  warn_500?: HTMLColor;
  warn_600?: HTMLColor;
  warn_700?: HTMLColor;
  warn_800?: HTMLColor;
  warn_900?: HTMLColor;
  warn_A100?: HTMLColor;
  warn_A200?: HTMLColor;
  warn_A400?: HTMLColor;
  warn_A700?: HTMLColor; 
}
```

## Action

This action changes the values of a theme given by the `id`.

## Permission

A user needs at least OML `can_manage_organization`.