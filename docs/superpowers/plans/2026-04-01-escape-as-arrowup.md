# Escape Key = ArrowUp Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the `Escape` key trigger the same "navigate to parent" behaviour as `ArrowUp`, replacing its current `showGrid` emit in `PhotoSlideshow`.

**Architecture:** `ArrowUp` is handled in `AppHeader.vue` and navigates to `parentRoute` (the closest ancestor breadcrumb with a `to`). `Escape` is currently handled in `PhotoSlideshow.vue` and emits `showGrid`, which calls `toGrid()` in the parent view — functionally equivalent but wired differently. The fix is to add `Escape` alongside `ArrowUp` in `AppHeader.vue` and remove it from `PhotoSlideshow.vue`.

**Tech Stack:** Vue 3, Vue Router, TypeScript. No frontend test framework is set up; verification is manual.

---

### Task 1: Add `Escape` to AppHeader keyboard handler

**Files:**
- Modify: `src/components/AppHeader.vue:81-86`

- [ ] **Step 1: Update the `onKeydown` function to handle `Escape` identically to `ArrowUp`**

In [src/components/AppHeader.vue](src/components/AppHeader.vue), replace:

```ts
function onKeydown(e: KeyboardEvent) {
  if (e.key === "ArrowUp" && parentRoute.value) {
    e.preventDefault();
    router.push(parentRoute.value);
  }
}
```

with:

```ts
function onKeydown(e: KeyboardEvent) {
  if ((e.key === "ArrowUp" || e.key === "Escape") && parentRoute.value) {
    e.preventDefault();
    router.push(parentRoute.value);
  }
}
```

- [ ] **Step 2: Verify manually**

Run `make serve` and open the photoblog or a gallery. Navigate into a photo. Press `Escape` — you should navigate to the grid (same as `ArrowUp`). Press `Escape` from the grid — nothing should happen (no `parentRoute` with a `to` at that level).

---

### Task 2: Remove `Escape` handler from PhotoSlideshow

**Files:**
- Modify: `src/components/PhotoSlideshow.vue:66-70`

Rationale: `AppHeader` now owns the `Escape` key globally. Keeping it in `PhotoSlideshow` would fire both handlers simultaneously, double-navigating.

- [ ] **Step 1: Remove the `Escape` branch from `onKeydown`**

In [src/components/PhotoSlideshow.vue](src/components/PhotoSlideshow.vue), replace:

```ts
function onKeydown(e: KeyboardEvent) {
  if (e.key === "ArrowLeft" && canPrev.value) emit("prev");
  else if (e.key === "ArrowRight" && canNext.value) emit("next");
  else if (e.key === "Escape") emit("showGrid");
}
```

with:

```ts
function onKeydown(e: KeyboardEvent) {
  if (e.key === "ArrowLeft" && canPrev.value) emit("prev");
  else if (e.key === "ArrowRight" && canNext.value) emit("next");
}
```

- [ ] **Step 2: Check `showGrid` emit is still used**

The `showGrid` emit is still triggered by the "Grid" button click (`@click="emit('showGrid')"`) in the template — so the emit definition and parent handler remain valid. No dead code.

- [ ] **Step 3: Verify manually**

Run `make serve`. Open a photo in the photoblog or a gallery. Confirm:
- `Escape` → navigates to parent (grid view)
- `ArrowLeft` / `ArrowRight` → still navigate between photos
- Clicking the "Grid" button → still works

- [ ] **Step 4: Commit**

```bash
git add src/components/AppHeader.vue src/components/PhotoSlideshow.vue
git commit -m "feat: escape key navigates to parent (same as ArrowUp)"
```
