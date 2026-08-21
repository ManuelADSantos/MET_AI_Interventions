# Task File Reference

This file documents all syntax supported by the task markdown parser.

---

## Structure

```
# Page Title              ← top-level heading = new page
> Block quote content      ← content block (paragraph, question text, etc.)
```

Each `#` heading starts a new page. Everything under it until the next `#` belongs to that page. Content inside `> ` block quotes is rendered as styled text.

---

## Question Types

Questions are defined with a `$type` directive indented with 4 spaces, placed after a `> ` content block. Append `?` to the type to make it optional (all questions are required by default).

### `$option` — Multiple choice

```markdown
> Pick one:

    $option; Choice A; Choice B; Choice C
```

Omit choices for Yes/No default:

```markdown
> Do you agree?

    $option
```

Add `Other` as a choice to allow free-text input:

```markdown
> Your field?

    $option; Engineering; Science; Other
```

Any option ending with `*` also triggers a free-text input, using the text before `*` as the label. Append a custom placeholder after `*`:

```markdown
> What is your favorite color?

    $option?;
    Red;
    Blue;
    Something else*Please describe
```

If no placeholder is given after `*`, the input shows empty. Both `Other` and `*` patterns can coexist across different questions.

### `$checkbox` — Multi-select checkboxes

Same syntax as `$option` but allows selecting multiple values. Stored as an array.

```markdown
> What is your gender?

    $checkbox;
    Woman;
    Man;
    Non-binary;
    Prefer not to disclose;
    Prefer to self-describe*
```

Supports `Other` and `*` free-text patterns just like `$option`.

### `$text` — Short text input

```markdown
> Describe briefly:

    $text
```

Validated: 3–200 characters.

### `$textarea` — Long text input

```markdown
> Explain your reasoning:

    $textarea
```

Validated: 2–400 characters.

### `$number` — Numeric input

```markdown
> How many do you expect?

    $number
```

Validated: integer, 0–999 by default. Custom bounds:

```markdown
> Pick a number between 5 and 42:

    $number; 5; 42
```

### `$slider` — Continuous slider

```markdown
> Rate your confidence:

    $slider; 0; 100; Not confident; Very confident
```

Format: `$slider; min; max; minLabel; maxLabel`

Defaults to 1–10 with "min"/"max" labels if parameters are omitted.

Append `tooltip` as an extra parameter to show the selected value while dragging, or `tooltip%` to add a percent sign:

```markdown
> What percentage of tasks will you finish?

    $slider; 0; 100; None; All; tooltip%
```

### `$likert` — Radio scale

```markdown
> How difficult was this?

    $likert; 1; 10; Very easy; Very difficult
```

Format: `$likert; min; max; minLabel; maxLabel`

Same parameter format as `$slider`. Renders as discrete radio buttons instead of a slider.

To label individual radio points, append text labels after the fourth parameter:

```markdown
> How often do you use AI?

    $likert; 1; 5; Never; Always; Never; Rarely; Sometimes; Often; Always
```

Labels map left-to-right to each radio button. If fewer labels are given than points, remaining points show their numeric value.

```markdown
> How often do you use AI?

    $likert; 1; 5; ; ; Never; Rarely; Sometimes; Often; Always
```

### Subtitles

Add a helper line beneath a question's title by placing a `~` line between the question text and the `$type` directive:

```markdown
> What is your profession?
~ e.g., health care worker, student, researcher ...

    $text?
```

Works with any question type. The subtitle is not included in the question text and does not count towards validation.

---

## Content Types

These are non-question elements rendered as static content.

### Headings

```markdown
> ## Subheading
```

Subheadings inside `>` blocks become styled headers (`##` = h3, `###` = h4, etc.).

### Images

```markdown
> ![alt text](image_url.png)
```

### Lists

```markdown
> - Item one
> - Item two
> - Item three
```

Ordered lists also supported:

```markdown
> 1. First
> 2. Second
```

### Tables

Standard markdown tables are supported:

```markdown
> | Column A | Column B |
> |----------|----------|
> | value 1  | value 2  |
```

### Paragraphs

Any `>` block without a `$` directive renders as a paragraph. Supports **bold**, *italic*, and other inline markdown.

---

## Tabs

Split a page into tabs with `:::tab Title`:

```markdown
# Page Title

:::tab Exercise

> Question goes here

    $option; A; B; C

:::tab Scenario

> Background info for the participant
```

The tab named **Exercise** (case-insensitive) is used as the main question content. If no tab is named "Exercise", the first tab is used.

---

## Copy Blocks

Define text that can be copied to the AI chat via the copy button:

```markdown
:::tab Scenario

:::copy
This text will be available via the copy button.
It can span multiple lines.
:::

> Visible content here
```

To disable the copy button on a specific tab:

```markdown
:::tab Instructions

:::no-copy

> This tab won't show a copy button.
```

`:::copy-disabled` also works.

---

## Chat & AI Prompt Directives

### `:::chat-enabled`

Show the chat panel on this page (only effective for conditions with chat, i.e. names not starting with `no-`):

```markdown
# Task Page

:::chat-enabled

:::tab Exercise

> Solve this problem.

    $option; A; B; C
```

### `:::require-ai-prompt`

Gate the Next button behind at least one AI prompt on a specific page:

```markdown
# Task Page

:::require-ai-prompt

:::tab Exercise

> Solve this problem.

    $option; A; B; C
```

Place `:::require-ai-prompt` anywhere in the page block. Only applies to conditions with chat enabled (conditions not starting with `no-`). Ignored in dev mode and on the last page.

### `:::predict-ai`

Hides the page's questions until the participant predicts whether the AI assistant would solve the task correctly (used by the `prediction` condition):

```markdown
# Task Page

:::predict-ai

:::tab Exercise

> Solve this problem.

    $option; A; B; C
```

The prediction is stored as response key `{sourceIndex}.prediction` (the numbered answers keep their ids) and logged as an `ai_prediction` interaction event.

---

## Sections & Randomization

### `%% RANDOMIZE`

Shuffles all pages inside a section:

```markdown
%% RANDOMIZE

# Question 1
> ...

# Question 2
> ...

%%
```

### `%% SECTION`

Marks a block as a section (preserves page order within):

```markdown
%% SECTION

# Q1
> ...

# Q2
> ...

%%
```

### `%% RANDOMIZE_SECTIONS`

Place on its own line (outside any section) to shuffle the order of all `SECTION` and `RANDOMIZE` blocks amongst themselves. Unmarked content (e.g., an intro page) stays in place.

```markdown
# Introduction
> Welcome text

%% RANDOMIZE_SECTIONS

%% RANDOMIZE
# Block A - Q1
> ...
# Block A - Q2
> ...
%%

%% RANDOMIZE
# Block B - Q1
> ...
# Block B - Q2
> ...
%%
```

---

## Full Example

```markdown
# Welcome

> Welcome to this study. Please read carefully.

> Do you consent to participate?

    $option; Yes, I agree

%% RANDOMIZE_SECTIONS

%% RANDOMIZE

# Task 1 (1/2)

:::tab Exercise

> **Is the following statement true?**

    $option; True; False

> How confident are you?

    $slider; 0; 100; Unsure; Certain

:::tab Scenario

:::copy
The event runs from 9am to 5pm with a 1-hour lunch break.
:::

> The event runs from 9am to 5pm with a 1-hour lunch break.

# Task 1 (2/2)

:::tab Exercise

> Describe your reasoning:

    $textarea

:::tab Context

> Same scenario as before.

%%

%% RANDOMIZE

# Task 2 (1/2)

:::tab Exercise

> Rate the difficulty:

    $likert; 1; 10; Very easy; Very difficult

:::tab Scenario

> Some other scenario text.

%%

# Final

> How many questions do you think you got right?

    $number

> Any feedback?

    $text?
```
