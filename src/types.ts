export interface ExifData {
  camera?: string;
  make?: string;
  lens?: string;
  focal_length?: string;
  aperture?: string;
  shutter_speed?: string;
  iso?: string;
  white_balance?: string;
  metering?: string;
  exposure_comp?: string;
}

export interface Photo {
  slug: string;
  /** Path prefix, e.g. "/photoblog/photos/20240615-093000". Append "-{size}.avif" etc. */
  base: string;
  sizes: number[];
  exif: ExifData;
  date: string;
  alt: string;
  caption: string;
}

export interface GalleryMeta {
  name: string;
  slug: string;
  /** Path prefix for the cover image. */
  cover_base: string;
  sizes: number[];
  count: number;
}
