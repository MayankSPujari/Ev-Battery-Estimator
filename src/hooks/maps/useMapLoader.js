import { useState, useEffect } from 'react';

/**
 * Custom hook to safely manage the loading lifecycle of the Google Maps Platform API.
 * Gracefully registers failures and handles resilient fallbacks to Leaflet.
 */
export const useMapLoader = () => {
  const [googleMapsLoaded, setGoogleMapsLoaded] = useState(false);
  const [loadError, setLoadError] = useState(false);
  const [isLeafletFallback, setIsLeafletFallback] = useState(false);

  useEffect(() => {
    // 1. If Google Maps is already loaded globally on window, bypass script injection
    if (typeof window !== 'undefined' && window.google && window.google.maps) {
      setGoogleMapsLoaded(true);
      return;
    }

    // 2. Safely read API Key from Vite Environment variables
    const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;

    if (!apiKey) {
      console.warn("VITE_GOOGLE_MAPS_API_KEY is missing in env. Activating Leaflet Fallback Mode.");
      setIsLeafletFallback(true);
      return;
    }

    // 3. Avoid duplicate script injections if another module loaded it concurrently
    const existingScript = document.getElementById('google-maps-api-script');
    if (existingScript) {
      setGoogleMapsLoaded(true);
      return;
    }

    // 4. Create and append the script tag dynamically
    const script = document.createElement('script');
    script.id = 'google-maps-api-script';
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places`;
    script.async = true;
    script.defer = true;

    script.onload = () => {
      setGoogleMapsLoaded(true);
      setLoadError(false);
    };

    script.onerror = (err) => {
      console.error("Google Maps API script failed to load. Activating Leaflet Fallback Mode.", err);
      setLoadError(true);
      setIsLeafletFallback(true);
    };

    document.head.appendChild(script);

    // 5. Cleanup
    return () => {
      // Keeping script mounted on window to avoid re-fetching
    };
  }, []);

  return { googleMapsLoaded, loadError, isLeafletFallback };
};
