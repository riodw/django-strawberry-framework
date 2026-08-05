# Security Policy

## Supported versions

`django-strawberry-framework` is in pre-1.0 development. Only the latest released version on `main` is supported with security fixes.

| Version  | Supported          |
| -------- | ------------------ |
| `0.x`    | :white_check_mark: |

The table is about *this* package. Its dependency floors are a separate question: `pyproject.toml` declares `Django>=5.2.16`, and Django `5.2.0`-`5.2.15` are not supported at all. Which Django releases carry security fixes is Django's own policy to state, not this project's.

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

### Resolver error masking is on by default under `DjangoSchema`

graphql-core returns the `str()` of any unhandled resolver exception in the response's top-level `errors[].message`, schema-wide — standard GraphQL behavior, not specific to this package. Since `0.0.17`, a schema constructed as `DjangoSchema` (required for generated mutations) resolves a **production error policy** at construction: under `settings.DEBUG = False`, an unexpected resolver or hook exception reaches the client as a stable non-sensitive message plus a `correlationId`, and the original exception is logged server-side under that same identifier. Parse/validation errors and deliberately raised `GraphQLError`s — the framework's audited rejections and permission denials included — keep their client-facing contract. The full shape, configuration (`error_policy=` / `ERROR_POLICY`), and per-event subscription coverage are in [the user guide's "Production error policy" section][docs-readme-error-policy].

Two configurations still put exception text on the wire, both deliberate: the explicit opt-out (`error_policy={"enabled": False}`), which is for consumers who own their own masking (Strawberry's `MaskErrors` extension or a `Schema.process_errors` override), and a plain `strawberry.Schema`, which never had the policy — a query-only schema built without `DjangoSchema` must bring its own masking.

### The `Django>=5.2.16` floor is a compatibility bound, not a secure-version recommendation

The Django floor in `pyproject.toml` is an API-compatibility statement frozen at release time — the oldest Django this package is written against — and never advice about which Django is safe to run. Deploy the **newest security patch in your chosen supported Django series** (`5.2.x` or `6.0.x`); that version moves past any floor this package can encode. The floor was deliberately set at a patched release (`5.2.16`, carrying the CVE-2026-48588 fix) so no supported configuration starts out behind a published advisory, but the next Django security release makes "the floor" and "the secure version" diverge again. The project's exact-floor CI cell is labelled `[compatibility floor]` for exactly this reason and is never a deployment target. Longer form: [the user guide's "Production security profile" section][docs-readme-production-profile].

### Production security profile

The consolidated deployment checklist — what the package already defaults to safe and how to verify each guarantee mechanically, the hardened mount recipe (IDE off, GET queries off, introspection disabled), transport body caps, CORS/cache/rate-limit posture, upload content responsibilities, why Relay `GlobalID`s are encodings rather than capabilities, and login/register throttling — lives in [the user guide's "Production security profile" section][docs-readme-production-profile]. Run Django's own `manage.py check --deploy` alongside it; the two lists deliberately do not overlap. The example project (`examples/fakeshop/`) is a development fixture that must never be deployed; its settings module fails loudly if loaded with `DEBUG` off.

## Disclosure

Once a fix is available we will publish a release and a corresponding GitHub Security Advisory. Reporters will be credited unless they request otherwise.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

[docs-readme-error-policy]: docs/README.md#production-error-policy
[docs-readme-production-profile]: docs/README.md#production-security-profile

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
