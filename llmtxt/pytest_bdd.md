# Pytest-BDD Best Practices Cheat Sheet

> A concise, field-tested reference for smooth day-to-day work with *
*pytest-bdd 8.x** & modern Python (3.11 +). Focus: IDE friendliness,
> fixture/step discovery, robust parsing, and cutting boilerplate while
> supporting advanced Gherkin features like **Scenario Outlines, Docstrings,
Datatables**.

---

## 1 · Project Layout & Boilerplate-Free Binding

* Keep feature files close to test code: `tests/bdd/features/…` under repo
  root (configure once in `pytest.ini`):

  `[pytest]\nbdd_features_base_dir = tests/bdd/features`

* Auto-bind all scenarios: In each test module:

  `from pytest_bdd import scenarios`
  `scenarios(".")  # bind every *.feature recursively`

* Selective manual binding: Put explicit `@scenario(...)` **before** the
  catch-all `scenarios()` call so IDEs resolve it & you can parametrize further

* Background reuse: Prefer **Background** for shared Given steps; avoid
  `conftest` “super fixtures” when simple background suffices

---

## 2 · Fixtures That Just Work ™

* **Centralize** reusable fixtures in `conftest.py`; IDEs index them once.
* Use **`target_fixture`** to override/alias inside a step:
  ```py
  @given("I am logged in", target_fixture="user")
  def _login(active_user):
      return active_user
  ```
  Only that scenario gets the override.
* Prefer **function-scope** unless you need broader caching; speeds up
  debugging.
* Avoid naming collisions: step arguments *aren’t* fixtures as of v6+; don’t
  rely on the old behaviour.
* Yield-style steps no longer auto-teardown - if you need cleanup, switch to a
  real fixture plus step wrapper.

---

## 3 · Writing Step Definitions the IDE Understands

- **One concept, one regex**- avoid similar phrases that compile to identical
  capture sets. Use `parsers.parse`/`cfparse` for readability & type safety;
  back it with `converters={}` for scenarios outlines so values aren’t just
  strings.
- **Multiple aliases** with stacked decorators, not copy-pasted functions.
- Keep functions **small, side-effect free**; push heavy lifting to
  helpers/fixtures so navigation shows meaningful code.
- For wildcard asterisk `*` continuation lines, still write a real
  Given/When/Then decorator - IDEs need the explicit mapping.

### Example (outline-ready & IDE-friendly)

```py
@given(parsers.parse("there are {start:d} cucumbers"), target_fixture="farm")
def cucumbers(start):
    return {"grow": start, "eaten": 0}
```

---

## 4 · Scenario Outlines & Example Tables

✔ Always use **angle-brackets** in the feature and **`parsers.*`** in
Python.<br>
✔ Attach a **converter** when you need non-string types (int, date).<br>
✔ Multiple Examples blocks? Use tags (`@positive`) and filter with
`pytest -k positive`.<br>
✔ Empty cells default to `""`; supply a custom converter if you want `None`.

---

## 5 · Docstrings & Datatables

* Access via the reserved arg names `docstring` or `datatable`.
* Respect indentation - internal lines are trimmed to the least indented line.
* Validate the presence of the block before relying on it to avoid errors.

```py
@then("the response should contain:")
def _(datatable):
    header, *rows = datatable
```

### General Tips

* Keep **one step = one function**; multi-decorator aliases break some language
  servers.
* Use **type hints** on fixture args; most IDEs will show them in tooltips.
* Run `pytest --generate-missing` to auto-create stub functions → IDE instantly
  recognizes them.

---

## 7 · Common Pitfalls & Quick Fixes

| Symptom                              | Root cause                                                            | Fix                                         |
|--------------------------------------|-----------------------------------------------------------------------|---------------------------------------------|
| `StepDefinitionNotFoundError`        | Typo or indentation mismatch in feature (all clauses must align left) | Align Given/When/Then, re-run tests         |
| Fixture "not found"                  | Forgot `target_fixture`, or defined fixture in non-imported module    | Add `target_fixture`, move to `conftest.py` |
| Outline params always str            | No converter specified                                                | `converters={"value": int}` or parse `:d`   |
| IDE shows *Undefined step reference* | Step files not within **Sources Root** or plugin missing              | Mark directory as *Sources*, install plugin |
| Values bleed between scenarios       | Shared mutable fixture at module scope                                | Use function-scope or copy object in step   |

---

## 8 · CI & Reporting

* Prefer `pytest --cucumberjson=report.json` + **cucumber-html-reporter** for
  dashboards.
* Add `--gherkin-terminal-reporter -vv` locally for readable progress.
* Pin pytest-bdd & pytest versions in `poetry.lock` or `requirements.txt` -
  breaking changes are frequent.

---

## 9 · Version-Specific Watch-outs (8.x)

* `docstring` & `datatable` arg names are **reserved**.
* Angular-bracket variables **only** parsed inside *Scenario Outline*.
* Dropped Python 3.8 support - check CI images.

---

## BDD Layout Rules

* Keep all feature files in the same directory as their step implementation.
* Step files must always start with `test_` so that pytest-bdd will find them.
* Always include `target_fixture` field on the given/when/then decorator, even
  if duplicative to the function name.
* Only test via the CLI in BDD tests - no direct API calls.
* Do not create extra binder files; keep `scenarios( ... )` in the main step
  module.
* Only test one feature per file to keep tests focused and maintainable.
