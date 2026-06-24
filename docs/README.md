# interrobang documentation

Welcome! These guides take you from your first app to a deep understanding of
how interrobang works.

![interrobang dashboard](images/hero.svg)

- **[Tutorial](tutorial.md)** — build a complete app from scratch, step by step.
- **[The Elm Architecture](architecture.md)** — models, messages, commands, and
  the event loop that ties them together.
- **[Styling guide](styling.md)** — colors, borders, padding, alignment, and the
  layout helpers.
- **[Components reference](components.md)** — every ready-made widget, with API
  and examples.
- **[Testing guide](testing.md)** — how to verify your app without a terminal.

If you prefer to learn by reading code, the [`examples/`](../examples) directory
has a runnable program for every feature.

## The shape of an app

interrobang has three parts, and the docs map onto them:

| Part | What it is | Guide |
| --- | --- | --- |
| the runtime (`Program`, model/update/view) | the event loop and app structure | [architecture](architecture.md) |
| the styling engine (`Style`, colors, borders) | text styling and layout | [styling](styling.md) |
| components (`Spinner`, `List`, ...) | ready-made widgets | [components](components.md) |

The guides assume no prior knowledge — start with the [tutorial](tutorial.md).
