# ADR-0012: pnpm 10 for the frontend, via corepack

**Date**: 2026-09-27
**Status**: accepted
**Deciders**: Praveen, AI assistant

## Context

The frontend was scaffolded with `create-next-app`, which installs with npm. The concern
that started this was supply-chain safety: packages on the public registry are sometimes
poisoned, and a poisoned package can run code on the developer's machine the moment it is
installed.

The first thing to be clear about is what a package manager cannot fix. npm, pnpm and yarn
all download from the same registry, so switching tools does not avoid a poisoned package.
The real difference is narrower and still worth having: by default, npm runs a package's
install scripts, and pnpm 10 does not — it blocks them unless the package is named in an
allow-list. Install scripts are how most registry attacks actually execute.

A second, smaller force: the repo's disk is chronically near full, and pnpm stores one copy
of each package version and links it into projects instead of copying.

## Decision

Use pnpm 10 for the frontend, activated through corepack so the version is pinned by the
repo rather than by whatever is installed on the machine. The npm lock file was removed and
replaced by a pnpm lock file.

## Alternatives Considered

### Alternative 1: Stay on npm
- **Pros**: nothing to change; the default for `create-next-app`; every guide assumes it.
- **Cons**: install scripts run by default, which is the step most registry attacks rely on.
- **Why not**: the safer default costs one switch, made once, early, on a project with
  almost no frontend code to disturb.

### Alternative 2: Yarn
- **Pros**: also supports stricter install behaviour.
- **Cons**: no advantage over pnpm here, and a heavier migration story.
- **Why not**: pnpm's blocked-by-default install scripts and its shared package store both
  fit this repo's needs directly.

### Alternative 3: Switch package manager and treat it as the security fix
- **Pros**: sounds decisive.
- **Cons**: it is not true. The registry is the same for all three tools.
- **Why not**: recorded here so nobody later believes this decision bought more safety than
  it did. Dependency review and lock files still do the heavier work.

## Consequences

### Positive
- Install scripts do not run unless a package is explicitly allowed.
- One shared package store instead of a copy per project, which matters on a near-full disk.
- The pnpm version is pinned by the repo through corepack, so every machine installs the
  same way.

### Negative
- Commands differ from the npm ones in most Next.js guides (`pnpm dev`, `pnpm build`).
- Corepack on an older machine may need updating before the pinned version activates.

### Risks
- A package that genuinely needs its install script fails quietly until it is allow-listed.
  Mitigated by pnpm naming the blocked package when it happens.
- False confidence that the registry risk is solved. Mitigated by Alternative 3 above,
  which states plainly that it is not.
