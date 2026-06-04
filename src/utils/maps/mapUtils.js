/**
 * Map coordinates and distance calculations utilities.
 */

/**
 * Calculate the Haversine distance between two coordinates in kilometers.
 * This is a highly resilient fallback that prevents dependency on the loaded Google Maps geometry library.
 */
export const calculateHaversineDistance = (lat1, lon1, lat2, lon2) => {
  const R = 6371; // Earth's radius in kilometers
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
};

/**
 * Decode OSRM coordinates path format to ensure it conforms perfectly to both engines.
 */
export const parseRoutePath = (rawRoute) => {
  if (!Array.isArray(rawRoute)) return [];
  return rawRoute.map((point) => {
    // If [lat, lng] format
    if (Array.isArray(point) && point.length === 2) {
      return { lat: Number(point[0]), lng: Number(point[1]) };
    }
    // If standard object format
    if (point && typeof point === 'object' && 'lat' in point && 'lng' in point) {
      return { lat: Number(point.lat), lng: Number(point.lng) };
    }
    return null;
  }).filter(Boolean);
};
