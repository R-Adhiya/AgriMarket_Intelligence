/**
 * CropImage — maps a crop name to a relevant agricultural image.
 *
 * Uses Unsplash Source free image URLs sized to the requested dimensions.
 * All images are public domain / free-to-use nature/food photography.
 * Falls back to a green placeholder with the crop initial if the image fails.
 *
 * Props:
 *   crop     {string}  Crop name (case-insensitive match)
 *   size     {number}  Pixel size for square images (default 80)
 *   className {string} Extra Tailwind classes on the <img>
 *   rounded  {string}  Tailwind rounding class (default "rounded-lg")
 */

// Curated Unsplash photo IDs for each crop.
// These are specific photo IDs that reliably resolve to agricultural content.
const CROP_IMAGES = {
  tomato:  "https://images.unsplash.com/photo-1546094096-0df4bcaaa337?w=120&h=120&fit=crop&auto=format&q=75",
  onion:   "https://images.unsplash.com/photo-1587049352851-8d4e89133924?w=120&h=120&fit=crop&auto=format&q=75",
  potato:  "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=120&h=120&fit=crop&auto=format&q=75",
  rice:    "https://images.unsplash.com/photo-1536304993881-ff86e0c9b1b5?w=120&h=120&fit=crop&auto=format&q=75",
  banana:  "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=120&h=120&fit=crop&auto=format&q=75",
  wheat:   "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=120&h=120&fit=crop&auto=format&q=75",
  maize:   "https://images.unsplash.com/photo-1551754655-cd27e38d2076?w=120&h=120&fit=crop&auto=format&q=75",
  corn:    "https://images.unsplash.com/photo-1551754655-cd27e38d2076?w=120&h=120&fit=crop&auto=format&q=75",
  chilli:  "https://images.unsplash.com/photo-1583119022894-919a68a3d0e3?w=120&h=120&fit=crop&auto=format&q=75",
  pepper:  "https://images.unsplash.com/photo-1583119022894-919a68a3d0e3?w=120&h=120&fit=crop&auto=format&q=75",
  mango:   "https://images.unsplash.com/photo-1605027990121-cbae9e0642df?w=120&h=120&fit=crop&auto=format&q=75",
  // generic farm fallback
  default: "https://images.unsplash.com/photo-1500937386664-56d1dfef3854?w=120&h=120&fit=crop&auto=format&q=75",
};

function getImageUrl(cropName) {
  if (!cropName) return CROP_IMAGES.default;
  const key = cropName.toLowerCase().trim();
  for (const [k, url] of Object.entries(CROP_IMAGES)) {
    if (k !== "default" && key.includes(k)) return url;
  }
  return CROP_IMAGES.default;
}

// Deterministic color from crop name for the fallback placeholder
function getPlaceholderColor(cropName) {
  const colors = [
    "bg-green-100 text-green-700",
    "bg-amber-100 text-amber-700",
    "bg-red-100 text-red-700",
    "bg-orange-100 text-orange-700",
    "bg-yellow-100 text-yellow-700",
    "bg-emerald-100 text-emerald-700",
  ];
  if (!cropName) return colors[0];
  const idx = cropName.charCodeAt(0) % colors.length;
  return colors[idx];
}

export default function CropImage({ crop, size = 80, className = "", rounded = "rounded-lg" }) {
  const url = getImageUrl(crop);
  const initial = (crop || "?")[0].toUpperCase();
  const placeholderColor = getPlaceholderColor(crop);

  return (
    <div
      className={`relative shrink-0 overflow-hidden ${rounded} ${className}`}
      style={{ width: size, height: size }}
    >
      <img
        src={url}
        alt={crop ? `${crop} crop` : "Agricultural produce"}
        width={size}
        height={size}
        loading="lazy"
        decoding="async"
        className="w-full h-full object-cover"
        onError={(e) => {
          // Hide broken image and show letter placeholder
          e.currentTarget.style.display = "none";
          e.currentTarget.nextSibling.style.display = "flex";
        }}
      />
      {/* Letter fallback — hidden by default, shown on image error */}
      <div
        className={`absolute inset-0 items-center justify-center text-lg font-bold ${placeholderColor}`}
        style={{ display: "none" }}
        aria-hidden="true"
      >
        {initial}
      </div>
    </div>
  );
}
