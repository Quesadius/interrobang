# tools

Developer scripts. These are **not** part of the published package — they exist
to maintain the project.

- **`termshot.py`** — a dependency-free ANSI→SVG renderer that turns terminal
  output into a styled "terminal window" SVG (still or animated).
- **`generate_images.py`** — regenerates every screenshot in `docs/images/` from
  the *real* output of interrobang's styling engine and components.

## Regenerating the documentation screenshots

After changing how a component or style looks, regenerate the images so the docs
stay accurate:

```bash
python tools/generate_images.py
```

This rewrites `docs/images/*.svg`. Commit the results alongside your change.
The SVGs are checked into the repo so they render on GitHub without a build step.
