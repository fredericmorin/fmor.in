# Photoblog History Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make prev/next photo navigation in photoblog and gallery views create browser history entries so the back/forward buttons navigate between photos.

**Architecture:** Both `PhotoblogView.vue` and `GalleryView.vue` use `router.replace` for prev/next navigation, which overwrites the current history entry. Changing to `router.push` makes each navigation create a new entry, enabling browser history traversal. No structural changes needed.

**Tech Stack:** Vue 3, Vue Router 4 (History API mode)

---

### Task 1: Fix photoblog prev/next to push history

**Files:**
- Modify: `src/views/PhotoblogView.vue:31-43`

- [ ] **Step 1: Change router.replace to router.push in prevPhoto and nextPhoto**

In `src/views/PhotoblogView.vue`, replace the two `router.replace` calls:

```ts
function prevPhoto() {
  const i = currentIndex.value;
  if (i !== null && i > 0) {
    router.push({ hash: `#${store.photos[i - 1].slug}` });
  }
}

function nextPhoto() {
  const i = currentIndex.value;
  if (i !== null && i < store.photos.length - 1) {
    router.push({ hash: `#${store.photos[i + 1].slug}` });
  }
}
```

- [ ] **Step 2: Verify manually**

Run: `make serve`

1. Open http://localhost:8000/photoblog/
2. Click any photo to open it
3. Click next a few times
4. Press browser back — should go to previous photo (not back to grid)
5. Press browser forward — should advance again
6. Press back repeatedly until before the first photo was opened — should return to grid

- [ ] **Step 3: Commit**

```bash
git add src/views/PhotoblogView.vue
git commit -m "feat: push history on photoblog prev/next navigation"
```

---

### Task 2: Fix gallery prev/next to push history

**Files:**
- Modify: `src/views/GalleryView.vue:36-48`

- [ ] **Step 1: Change router.replace to router.push in prevPhoto and nextPhoto**

In `src/views/GalleryView.vue`, replace the two `router.replace` calls:

```ts
function prevPhoto() {
  const i = currentIndex.value;
  if (i !== null && i > 0) {
    router.push({ hash: `#${photos.value[i - 1].slug}` });
  }
}

function nextPhoto() {
  const i = currentIndex.value;
  if (i !== null && i < photos.value.length - 1) {
    router.push({ hash: `#${photos.value[i + 1].slug}` });
  }
}
```

- [ ] **Step 2: Verify manually**

1. Open any gallery (e.g. http://localhost:8000/gallery/some-gallery/)
2. Click any photo to open it
3. Navigate next a few times
4. Press browser back — should go to previous photo
5. Press back to before the gallery was opened — should return to grid

- [ ] **Step 3: Commit**

```bash
git add src/views/GalleryView.vue
git commit -m "feat: push history on gallery prev/next navigation"
```
