# Extraction Contract

Mindgarden is physically colocated with Empathy while its responsibilities
mature, but it must remain independently extractable.

## Required invariants

- Reusable source stays beneath `mindgarden/`.
- Mindgarden source does not import files from its parent repository.
- Consumer knowledge stays in the repository-root `.garden/`, not inside the
  reusable source directory.
- Public interfaces are versioned contracts or documented commands.
- Mindgarden tests and fixtures stay beneath `mindgarden/`.
- Empathy-specific integration tests may live in Empathy's root test surface.
- Third-party code and assets require recorded provenance and license review.

## Future extraction

When the holon is ready for independent release, its directory history can be
projected from a disposable clone with `git filter-repo`:

```bash
git filter-repo \
  --path "mindgarden/" \
  --path-rename "mindgarden/:"
```

The extracted repository must then receive its standalone release, CI, and
consumer compatibility configuration before Empathy switches from colocated
source to a pinned dependency.
