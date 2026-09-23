# Owner Authentication

The initial platform is private and single-owner. Authentication is
self-hosted so this milestone does not silently select an external identity
provider.

## Bootstrap And Credentials

- `OwnerAuth.bootstrap_owner` is a one-time operator action. A database-level
  singleton constraint prevents concurrent creation of a second owner.
- Email is normalized before persistence.
- Passwords must contain 12 to 1024 characters. They are stored as salted
  scrypt verifiers; plaintext is never persisted.
- Login failures use one generic response for unknown owner, invalid email,
  wrong password, and disabled account.

There is no default password, signup endpoint, password-reset email, OAuth
provider, or committed credential. Production bootstrap credentials must be
provided through an operator-controlled secret channel outside logs and source
control.

## Sessions

- Login creates a cryptographically random opaque token.
- The raw token is returned once and its representation is redacted.
- PostgreSQL stores only the SHA-256 token digest, issue/expiry timestamps, last
  seen time, and revocation state.
- Session lifetime is configurable from 5 minutes to 30 days and defaults to 12
  hours.
- Password change and owner disable revoke every active session.

The FastAPI ticket owns secure cookie/header transport, CSRF behavior, and
HTTP error mapping. Public deployment still requires TLS, rate limits, audit
events, secret rotation, recovery procedures, and a reviewed threat model.

## Authorization Boundary

Authentication produces an `OwnerPrincipal`. API and service calls must derive
`owner_id` from that principal rather than accept an owner supplied in a URL or
request body. Existing owner-scoped repositories remain the data-authorization
boundary. No broker or execution permission is introduced.
