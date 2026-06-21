# interrobang documentation

Welcome! These guides take you from your first app to a deep understanding of
how interrobang works.

- **[Tutorial](tutorial.md)** — build a complete app from scratch, step by step.
- **[The Elm Architecture](architecture.md)** — models, messages, commands, and
  the event loop that ties them together.
- **[Styling guide](styling.md)** — colors, borders, padding, alignment, and the
  layout helpers (the Lip Gloss side of interrobang).
- **[Components reference](components.md)** — every ready-made widget, with API
  and examples.
- **[Testing guide](testing.md)** — how to verify your app without a terminal.

If you prefer to learn by reading code, the [`examples/`](../examples) directory
has a runnable program for every feature.

## A note on terminology

interrobang borrows its vocabulary from [Charm](https://charm.sh)'s Go libraries:

| interrobang | Charm equivalent | What it is |
| --- | --- | --- |
| the runtime (`Program`, model/update/view) | Bubble Tea | the event loop and app structure |
| the styling engine (`Style`, colors, borders) | Lip Gloss | text styling and layout |
| components (`Spinner`, `List`, ...) | Bubbles | ready-made widgets |

If you know those libraries, you'll feel at home. If you don't, you don't need
to — these guides assume no prior knowledge.
