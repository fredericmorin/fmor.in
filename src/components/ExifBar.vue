<script setup lang="ts">
import { computed } from "vue";
import type { ExifData } from "@/types";

const props = defineProps<{
  exif: ExifData;
  date: string;
}>();

const fields = computed(() => {
  const out: string[] = [];
  const e = props.exif;
  if (e.camera) out.push(e.camera);
  if (e.lens) out.push(e.lens);
  if (e.focal_length) out.push(`${e.focal_length}mm`);
  if (e.aperture) out.push(`ƒ/${e.aperture}`);
  if (e.shutter_speed) out.push(`${e.shutter_speed}s`);
  if (e.iso) out.push(`ISO ${e.iso}`);
  return out;
});

const hasData = computed(() => fields.value.length > 0 || props.date);
</script>

<template>
  <div v-if="hasData" class="flex items-center gap-3 px-4 py-2 border-t border-neutral-800 text-xs text-neutral-500 overflow-x-auto whitespace-nowrap">
    <span v-if="date" class="text-neutral-400 shrink-0">{{ date }}</span>
    <span v-if="date && fields.length" class="text-neutral-700">·</span>
    <span v-for="(field, i) in fields" :key="i" class="shrink-0">
      <span v-if="i > 0" class="mr-3 text-neutral-700">·</span>{{ field }}
    </span>
  </div>
</template>
