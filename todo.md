# TODO

This file records the current state of the library, the design decisions already made, and the next work items in a sensible order.

## Project snapshot

The codebase is now a small VT-oriented TUI core with:

- a backend split (`_posix.py`, `_win.py`, `lc_platform.py`)
- a byte-oriented input path with VT key decoding
- a screen state layer (`lc_screen.py`)
- a window model with dirty tracking (`lc_window.py`)
- a batched renderer (`lc_refresh.py`)
- subwindows with shared backing store
- panel helpers and panel-content subwindow helpers
- explicit resize handling through `LC_KEY_RESIZE`

The project is no longer a rough ANSI experiment. It now has a real internal architecture and a usable contract surface.

## Design decisions already made

### Terminal model
- The library is VT/ANSI oriented.
- Output is escape-sequence based.
- Input is byte-oriented and decoded in the core.
- Windows support is provided through a backend, not by pretending Windows is POSIX.

### Backend contract
- Backends must implement the API declared in `lc_platform.py`.
- The core owns rendering and key decoding.
- The backend owns terminal mode setup, raw/cbreak/echo toggles, byte input, and resize observation.

### Window model
- `LCWin` is the central window object.
- Rows store dirty spans (`firstch`, `lastch`, `flags`).
- Clipping is explicit and helper-based.
- Drawing helpers operate on clipped geometry instead of assuming full visibility.

### Subwindow model
- Subwindows share backing store with their parent.
- Dirty changes propagate upward through the parent chain.
- Subwindows are parent-relative at creation time.
- Each window tracks `parent`, `root`, `pary`, `parx`, `alive`, and `children`.

### Lifecycle model
- Windows are either alive or dead.
- Freeing a parent recursively frees its subtree.
- Operations on dead windows fail.
- Subwindows do not survive parent teardown.

### Resize model
- A root resize invalidates all derived subwindows.
- The application is expected to rebuild subwindows after receiving `LC_KEY_RESIZE`.
- This is intentional. The library does not currently attempt to remap derived windows across a resize.

### Panel model
- A panel is currently a composed drawing operation:
  - box
  - optional title
  - optional interior fill
- Panel content geometry is defined by the box interior.
- Panel content may be accessed through a derived subwindow.

## What is stable enough right now

These areas are in decent shape and can be treated as the current base:

- backend split and backend contract
- basic terminal mode switching
- alternate screen usage
- dirty-row rendering with batching
- clipping helpers for rects and spans
- box, line, fill, title, and panel primitives
- shared-backing subwindows
- recursive free and child invalidation
- resize -> `LC_KEY_RESIZE` flow

## Known technical weaknesses

These are the most important current weaknesses, not vague future dreams.

### 1. Refresh path does not guard dead windows strongly enough
`lc_wrefresh()` should reject dead windows immediately.

Current risk:
- dead windows may have `lines == []`
- stale callers may still pass them into refresh
- this can lead to index errors or undefined rendering behavior

### 2. Cursor semantics at the bottom-right corner are awkward
`_advance_cursor()` currently uses an out-of-range row sentinel on final wrap.

This works, but it is not clean.
The project should choose one explicit model:

- saturating cursor at last valid cell, or
- private end-of-window state that does not leak through `cury`/`curx`

### 3. Refresh semantics for subwindows are not documented sharply enough
It should be stated clearly whether `lc_wrefresh(subwin)` is a first-class supported operation or merely something that happens to work.

### 4. Bulk write paths are slightly split
Some operations use `_set_cell()`, while `_write_text_clipped()` performs direct row writes and then marks dirty.
This is not broken, but it is a maintenance smell.
A cleaner internal bulk-write path would reduce drift.

### 5. Resize rebuild flow should be documented as an application recipe
The core behavior is correct enough, but the expected app-side rebuild sequence should be stated more concretely.

## Immediate next tasks

These are the next sensible tasks in order.

### Priority 1: close correctness gaps
- [ ] Add an `alive` guard at the start of `lc_wrefresh()`.
- [ ] Audit refresh-adjacent helpers for dead-window assumptions.
- [ ] Add tests that explicitly verify refresh on dead windows fails cleanly.

### Priority 2: fix cursor semantics
- [ ] Choose and document the cursor model at the last cell.
- [ ] Update `_advance_cursor()` and write paths accordingly.
- [ ] Add tests for:
  - final-column write
  - final-cell write
  - repeated writes after last writable cell

### Priority 3: lock down subwindow refresh semantics
- [ ] Decide whether subwindow refresh is first-class API behavior.
- [ ] Document that decision in `README.md` and `todo.md`.
- [ ] Add tests that match the chosen rule.

## Next structural tasks

Once the immediate correctness gaps are closed, these are the next worthwhile structural improvements.

### Geometry and layout
- [ ] Add simple layout helpers for vertical and horizontal splits.
- [ ] Consider a small rect helper module if geometry keeps growing.
- [ ] Keep clipping policy centralized and test-driven.

### Panel/content workflow
- [ ] Add optional header-band support for panels.
- [ ] Decide whether headers are visual only or define a separate content origin.
- [ ] If headers become real layout regions, add helper(s) for header/body rect extraction.

### Rendering
- [ ] Review whether dirty tracking plus hash tracking is redundant in some hot paths.
- [ ] Consider a more explicit row-level bulk emit helper.
- [ ] Add regression tests for large dirty spans and clipped redraws.

### Input
- [ ] Add more explicit tests for ALT-modified input.
- [ ] Add tests for ESC timing behavior.
- [ ] Decide how far function-key compatibility should go across terminals.

### Backend discipline
- [ ] Add backend contract tests where practical.
- [ ] Keep Windows behavior byte-oriented and explicit.
- [ ] Avoid introducing POSIX assumptions into the generic core.

## Larger future work

These are real future items, but not the next thing to touch.

### Window hierarchy evolution
- [ ] Decide whether to add true derived-window variants beyond the current `lc_subwin()` model.
- [ ] Decide whether child windows should ever be automatically recreated across resize.
- [ ] If automatic remapping is ever considered, write the invariants first before touching code.

### Attributes and styling
- [ ] Extend attributes beyond bold/underline/reverse only if the terminal contract stays clear.
- [ ] Decide whether colors belong in the same attr model or in a separate encoding layer.

### API shaping
- [ ] Clean up naming once the core stabilizes.
- [ ] Decide project name based on what the library actually is, not what sounds cute.
- [ ] Keep the public API small until semantics are fully nailed down.

## Rules to keep while moving forward

- Do not add features that blur backend/core responsibilities.
- Do not add convenience helpers that hide unresolved semantics.
- Do not preserve subwindows across resize unless the full remap contract is designed first.
- Prefer explicit invalidation and rebuild over clever hidden behavior.
- Keep tests focused on contracts and invariants, not just happy-path screenshots.

## Working definition of the project

For now, the most accurate description is:

> A small, explicit, VT-oriented TUI core for Python with backend abstraction,
> byte-oriented input decoding, dirty-region rendering, and a lightweight
> shared-backing window model.

That is a much better north star than trying to be a generic clone of curses.
