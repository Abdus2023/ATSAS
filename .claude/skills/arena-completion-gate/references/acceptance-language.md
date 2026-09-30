# Acceptance Expression Language (`acceptance-language.md`)

- **Component**: `C-07` (`arena-completion-gate`)
- **Schema**: [`../../_shared/aif/schema/acceptance-expression.schema.json`](../../_shared/aif/schema/acceptance-expression.schema.json)

---

## 1. Grammar (`10.3`)

```text
AcceptanceExpression =
    ALL(expressions[])
  | ANY(expressions[])
  | AT_LEAST_N(n, expressions[])
  | OPTIONAL(expression)
  | CONDITIONAL(condition, then, else)
  | CLAIM(claim_id)
```

---

## 2. Evaluation Semantics (`10.15`)

| Operator | Rule |
|---|---|
| `CLAIM(c)` | Evaluates verification state of claim `c` at `evaluated_snapshot` (`VERIFIED` + `snapshot_match=MATCH` + `scope_match=MATCH` $\implies$ `SATISFIED`; `CONTRADICTED` $\implies$ `CONTRADICTED`; otherwise `UNSATISFIED`) |
| `ALL(xs)` | Evaluates every `x` in `xs`. If any `CONTRADICTED` $\implies$ `CONTRADICTED`; else if any `UNSATISFIED` $\implies$ `INCOMPLETE`; else `SATISFIED` |
| `ANY(xs)` | Evaluates every `x` in `xs`. If any `SATISFIED` $\implies$ `SATISFIED`; else if all `CONTRADICTED` $\implies$ `CONTRADICTED`; else `INCOMPLETE` |
| `AT_LEAST_N(n, xs)` | Counts `SATISFIED` elements in `xs`. If `count >= n` $\implies$ `SATISFIED`; else `INCOMPLETE` |
| `OPTIONAL(x)` | Evaluates `x` for trace recording; always returns `SATISFIED` unless `CONTRADICTED` |
| `CONDITIONAL(cond, then_expr, else_expr)` | Evaluates `cond`; if `SATISFIED`, evaluates `then_expr`, else evaluates `else_expr` |
