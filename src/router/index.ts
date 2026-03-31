import { createRouter, createWebHistory } from "vue-router";
import PhotoblogView from "@/views/PhotoblogView.vue";
import GalleryIndexView from "@/views/GalleryIndexView.vue";
import GalleryView from "@/views/GalleryView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/photoblog/" },
    { path: "/photoblog/", component: PhotoblogView },
    { path: "/gallery/", component: GalleryIndexView },
    { path: "/gallery/:name/", component: GalleryView },
  ],
  // Don't scroll on hash changes (photo navigation); only scroll on path changes
  scrollBehavior(to, from) {
    if (to.path !== from.path) return { top: 0 };
    return false;
  },
});

export default router;
