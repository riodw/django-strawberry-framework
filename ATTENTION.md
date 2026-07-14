# Attention: GraphQL names at the optimizer boundary

## Status

Revisit this topic after local-diff group **#10** is complete.

The immediate correctness fix is currently staged in the optimizer-walker group. This file is a
follow-up marker, not part of that staged commit. The remaining question is whether schema naming
configuration should become available earlier than Strawberry schema construction so the framework
can validate custom-name collisions during `finalize_django_types()`.

## Why this needs attention

The package advertises four behaviors that meet at the same boundary:

1. A [`DjangoType`][glossary-djangotype] exposes selected Django model fields through Strawberry.
2. Consumer-authored `strawberry.field(...)` overrides are preserved.
3. [`strawberry_config(...)`][glossary-strawberry-config] forwards Strawberry configuration such as
   `auto_camel_case` and a custom `NameConverter`.
4. [`DjangoOptimizerExtension`][glossary-optimizer] maps selected GraphQL fields back to Django ORM
   names to build `.only()`, `select_related()`, and `prefetch_related()` plans, including windowed
   planning for synthesized relation connections.

Those promises require one reliable GraphQL-name-to-Python-name boundary. The old walker treated
`snake_case(selection.name)` as that boundary. That works for ordinary default-camel-cased names,
but it is not a general inverse of Strawberry's naming process.

## The underlying issue

GraphQL naming can be lossy or deliberately non-reversible:

| Python or Django name | GraphQL name | Reverse result | Actual ORM name |
| --- | --- | --- | --- |
| `address_2` | `address2` | `address2` | `address_2` |
| `address_line_2` | `addressLine2` | `address_line2` | `address_line_2` |
| `line_2_connection` | `line2Connection` | `line2_connection` | `line_2_connection` |
| `postal_code` with `name="secondaryAddress"` | `secondaryAddress` | `secondary_address` | `postal_code` |

An underscore before a digit disappears under Strawberry's default camelizer. No reverse function
can determine whether `address2` came from `address2` or `address_2`. An explicit GraphQL name or a
custom `NameConverter` can produce an arbitrary valid GraphQL name, so reversal is not even the
right abstraction for those cases.

The authoritative direction is forward:

```text
real Python/Django field
    -> finalized StrawberryField metadata
    -> active schema NameConverter
    -> selected GraphQL name
```

## The confirmed bugs

The old reverse-only lookup caused several related optimizer failures:

- A digit-boundary scalar could be omitted from `.only(...)`, leaving it deferred and causing a
  lazy query when Strawberry resolved the field.
- A digit-boundary foreign key or one-to-one field could be omitted from `select_related(...)`,
  causing a per-parent N+1.
- A synthesized digit-boundary `<field>Connection` could be missed entirely, so its advertised
  windowed `Prefetch` became one connection query per parent.
- A target primary key such as `code_2` could miss the FK-ID-elision path. This remained correct but
  performed an unnecessary join.
- An explicitly named `strawberry.field(...)` could be invisible to optimizer planning even though
  consumer overrides are a documented package feature.
- Selection merging used `snake_case(selection.name)` as its identity. Two distinct GraphQL fields
  such as `secondaryAddress` and `secondary_address` therefore collapsed into one selection, and
  one ORM field could disappear from the plan.
- A custom schema `NameConverter`, accepted through `strawberry_config(...)`, could produce names
  the optimizer could not map back to the registered `DjangoType`.

GraphQL results usually remained correct because Django lazily loaded the missing data. The visible
failures were extra queries, broken optimizer guarantees, and possible false `strictness="raise"`
errors for supported fields. The nested-connection case directly contradicted the documented
one-batched-query-per-relation behavior.

## The staged fix

[`optimizer/walker.py`][walker] now owns one shared selection-name resolver for both model fields
and synthesized relation connections:

1. Keep the existing `snake_case(...)` dictionary lookup as the fast path for ordinary names.
2. On a miss, read the finalized Strawberry fields from the resolved `DjangoType`.
3. Resolve their actual GraphQL names through the active schema `NameConverter` carried by execution
   `info`.
4. Fall back to Strawberry's default forward camelizer only for unregistered or synthetic internal
   planner calls where no authoritative Strawberry field exists.
5. Return the real Django field name, never a guessed reverse name, for ORM planning.

The same forward-resolution path now covers:

- scalar projection;
- forward and reverse relation planning;
- synthesized relation-connection recognition;
- FK-ID elision;
- explicit `strawberry.field(name=...)` names; and
- custom schema name converters.

Selection merging now keys on the exact GraphQL field name. Aliases of the same field still merge
because their `selection.name` is identical, while distinct GraphQL names remain distinct even when
`snake_case(...)` would collapse them.

The fix does **not** rename public GraphQL fields, change the default camel-casing convention, or
change the `DjangoType` declaration API. It makes optimizer planning follow the schema Strawberry
actually built.

## The remaining limitation

`finalize_django_types()` runs before `strawberry.Schema(...)` exists. Therefore it cannot see the
schema's eventual custom `NameConverter`.

The finalizer can proactively detect Python-name collisions and collisions produced by Strawberry's
default camelizer. A collision created only by a custom converter cannot be detected at that phase.
Strawberry detects it later while constructing the schema and raises its schema-build duplicate-field
error.

For example, if a custom converter maps both `primary_address` and `shipping_address` to `address`,
the framework cannot attribute that collision during finalization because it has not yet received the
converter. The schema still fails loudly; the difference is the timing and quality of the error.

There is one related internal boundary: a direct call to the private
`optimizer.walker.plan_optimizations(..., info=None)` cannot know an active custom schema converter.
The public `DjangoOptimizerExtension` path always supplies execution `info`, and
`plan_optimizations` is deliberately not re-exported as consumer API, so this does not limit an
advertised feature.

## Real-world example 1: how I thought it worked

Consider a delivery application with a conventional second address line and a numbered reverse
relation retained from a legacy database:

```python
class ShippingAddress(models.Model):
    address_line_1 = models.CharField(max_length=100)
    address_line_2 = models.CharField(max_length=100, blank=True)


class DeliveryAttempt(models.Model):
    address = models.ForeignKey(
        ShippingAddress,
        related_name="delivery_attempt_2",
        on_delete=models.CASCADE,
    )


class ShippingAddressType(DjangoType):
    class Meta:
        model = ShippingAddress
        fields = ("id", "address_line_1", "address_line_2", "delivery_attempt_2")
        interfaces = (relay.Node,)
```

A consumer reasonably expects this query:

```graphql
{
  shippingAddresses {
    addressLine2
    deliveryAttempt2Connection(
      first: 3
    ) {
      edges {
        node {
          id
        }
      }
    }
  }
}
```

to produce a projection containing `address_line_2` and one batched windowed prefetch for
`delivery_attempt_2`. The mental model was that camel-casing and snake-casing were inverse operations,
so every selected GraphQL name would return to its Django field automatically.

Before the fix, `addressLine2` reversed to `address_line2`, and `deliveryAttempt2Connection`
reversed to `delivery_attempt2_connection`. Neither matched the actual metadata keys. The scalar was
deferred and the connection was unplanned, even though the query and schema were valid.

## Real-world example 2: how it actually works now

The same schema and query keep their existing public names. The optimizer first attempts its ordinary
fast lookup. When that misses, it asks the finalized Strawberry fields what GraphQL names the active
schema converter assigned:

```text
address_line_2
    -> StrawberryField(python_name="address_line_2")
    -> "addressLine2"
    -> selected name matches
    -> .only("address_line_2")

delivery_attempt_2_connection
    -> synthesized StrawberryField
    -> "deliveryAttempt2Connection"
    -> selected name matches
    -> Prefetch("delivery_attempt_2", to_attr="_dst_delivery_attempt_2_connection")
```

This also works if the application explicitly exposes `address_line_2` as `secondaryAddress`, or if
a custom `NameConverter` chooses that name globally. Planning follows the actual schema name forward
to the real ORM field instead of trying to reconstruct the ORM name from GraphQL text.

If two selected fields are explicitly named `secondaryAddress` and `secondary_address`, they now
remain two independent selections. Exact GraphQL identity controls merging, so both underlying ORM
columns appear in the plan.

## Questions to revisit after #10

1. Should `finalize_django_types()` accept the intended `StrawberryConfig` or `NameConverter` so
   custom-converter collision errors can be framework-attributed earlier?
2. Would threading schema configuration into finalization create an undesirable ordering or lifecycle
   dependency?
3. Should the public documentation explicitly state that custom-only name collisions are detected at
   Strawberry schema construction rather than framework finalization?
4. Is the current private-call fallback sufficient, or should `plan_optimizations` accept an explicit
   converter for internal tooling and isolated tests?
5. Should a live GraphQL acceptance test pin the custom-converter path in addition to the focused
   walker regression tests?

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary-djangotype]: docs/GLOSSARY.md#djangotype
[glossary-optimizer]: docs/GLOSSARY.md#djangooptimizerextension
[glossary-strawberry-config]: docs/GLOSSARY.md#strawberry_config

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[walker]: django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
