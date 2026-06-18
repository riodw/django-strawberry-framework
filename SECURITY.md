# Security Policy

## Supported versions

`django-strawberry-framework` is in pre-1.0 development. Only the latest released version on `main` is supported with security fixes.

| Version  | Supported          |
| -------- | ------------------ |
| `0.x`    | :white_check_mark: |

## Reporting a vulnerability

If you discover a security vulnerability, **please do not open a public issue**.

Instead, report it privately by either:

- Using GitHub's [private vulnerability reporting](https://github.com/riodw/django-strawberry-framework/security/advisories/new) on this repository, or
- Emailing the maintainer at `riodweber@gmail.com` with the subject line `SECURITY: django-strawberry-framework`.

Please include:

- A description of the vulnerability and its impact.
- Steps to reproduce, or a minimal proof-of-concept.
- Affected versions, if known.
- Any suggested mitigation.

You can expect an initial response within **7 days**. We will work with you to validate the issue, prepare a fix, and coordinate a disclosure timeline.

## Deployment hardening

### Mask resolver errors in production

graphql-core returns the `str()` of any unhandled resolver exception in the response's top-level `errors[].message`, schema-wide — this is standard GraphQL behavior, not specific to this package. The framework's own write-authorization path raises a controlled `GraphQLError("Not authorized to <op> <Type>.")` that reveals nothing the client did not already send, but a **consumer-supplied** hook (a `get_queryset`, a `check_permission` / `permission_classes` `has_permission`, a custom resolver) that raises will surface its exception message to the client.

In production, configure Strawberry's error masking so resolver/permission exception messages are not returned to clients — for example the `MaskErrors` schema extension, or a `Schema.process_errors` override. This is the GraphQL equivalent of running Django with `DEBUG=False`, and applies to any GraphQL deployment regardless of this package.

## Disclosure

Once a fix is available we will publish a release and a corresponding GitHub Security Advisory. Reporters will be credited unless they request otherwise.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
