# Contract: user interface

One page, one centred card (max 560 px), fluid down to 360 px. Russian texts.

## Layout (top → bottom)

1. **Header** — logo, title «Конвертер валют», subtitle «Официальные курсы Национального банка
   Молдовы», theme switch (☀/☾; follows the system until the user chooses).
2. **Status banner area** — zero or more banners (`info` blue, `warning` amber, `error` red), each
   with an icon, text and optional actions.
3. **Amount** — large numeric text field (`inputmode="decimal"`), label «Сумма», placeholder «0»,
   error text below the field.
4. **Currency row** — «Из» picker · round swap button (⇄, rotates on click) · «В» picker. Each picker
   shows a coloured badge with the currency symbol, code and name; opens a searchable list
   (search by code/name, popular currencies on top: MDL, EUR, USD, RON, UAH, RUB, GBP; per-unit
   rate to MDL on the right); keyboard: ↑/↓, Enter, Esc.
5. **Date** — date field «Дата курса» (min 2000-01-01, max tomorrow) + chip «Сегодня».
6. **Convert button** — full width, disabled until amount, both currencies and date are filled;
   shows a spinner while loading. Enter in the amount field = click.
7. **Result card** (hidden until the first result; hidden again on error):
   - «100 Доллар США =» (small) / «1 833,83 MDL» (large, tabular digits) + copy button;
   - «1 USD = 18,3383 MDL · 1 MDL = 0,0545 USD»;
   - meta chips: «Курс на 18.11.2026» and source chip — green dot «НБМ · bnm.md» (live) or amber
     dot «Сохранённая копия · сохранено 18.11.2026 12:30» (saved).
8. **Footer** — «Данные: Национальный банк Молдовы (bnm.md). Курс публикуется в рабочие дни до 13:00
   и действует весь следующий рабочий день.»

## States

| State | What the user sees |
|-------|--------------------|
| Loading rates (start) | skeleton shimmer on pickers, button disabled |
| Ready | form enabled |
| Converting | button spinner; inputs stay editable; only the latest response is applied |
| Result | result card animates in |
| Field error | red outline + message under the field + gentle shake; result hidden |
| Weekend / not published | blue banner with requested and used dates; result shown |
| Offline, saved copy exists | amber banner «Нет связи с НБМ…» + buttons «Использовать сохранённый курс от DD.MM.YYYY» / «Повторить» |
| Saved-copy mode | amber banner «Работаем с сохранённой копией…» + button «Попробовать онлайн»; source chip amber |
| Offline, nothing saved (start) | empty-state card with illustration, text and «Повторить» instead of the form |
| Unexpected error | red banner with «Повторить» |

## Accessibility & motion

Labels bound to inputs, `aria-live="polite"` for result and banners, visible focus rings, contrast
≥ 4.5:1 in both themes, `prefers-reduced-motion` disables animations.
