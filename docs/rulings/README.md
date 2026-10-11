# Rulings

`log.yaml` records every decision the maintainer made that an agent could not: a methodology call,
a data-handling rule, how a class of cases is handled from now on. It exists so that a settled
question is never asked twice, and so that an agent applying a ruling can cite it.

It is a record, not a reference document. A ruling that changes a rule is written into that rule's
home (a reference document, the methodology, a workflow, the code), and the entry points at that
home with `lands_in`. The log says who decided what and why; the home says what the rule is.

## An entry

```yaml
- id: R-2026-10-11-a          # R-<date>-<letter>, unique, never reused
  date: "2026-10-11"          # when it was decided, quoted
  by: lspdrz                  # GitHub handle of the person who decided
  venue: session              # session | issue | pr-review
  refs: []                    # issues, PRs or records it concerns
  question: >-
    What was asked, precisely enough to recognize when it comes round again.
  ruling: >-
    The decision, stated as a decision.
  reasoning: >-               # optional; the decider's reason
  status: in-force            # in-force | deferred | replaced
  executor: none              # agent | maintainer | none: who still has to carry it out
  lands_in: []                # repository paths that now state the rule
  applied_in: []              # PRs that carried it out
  replaced_by:                # the id of the replacing ruling, when status is replaced
```

Rules that `tests/test_rulings.py` enforces:

- Entries are appended in date order and never deleted. A changed ruling gets a new entry; the old
  one moves to `status: replaced` with `replaced_by` naming the new id. That, and filling in
  `lands_in` and `applied_in`, are the only edits an existing entry may receive.
- A `deferred` entry was asked and not answered; its `reasoning` says why.
- Every `lands_in` path exists.
