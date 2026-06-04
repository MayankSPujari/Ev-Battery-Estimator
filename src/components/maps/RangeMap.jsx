import React, { useEffect, useRef, useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useMapLoader } from '../../hooks/maps/useMapLoader';
import { calculateHaversineDistance, parseRoutePath } from '../../utils/maps/mapUtils';

// Premium Cyber Dark styles for Google Maps
const DARK_MAP_STYLE = [
  { elementType: "geometry", stylers: [{ color: "#0d1117" }] },
  { elementType: "labels.icon", stylers: [{ visibility: "off" }] },
  { elementType: "labels.text.fill", stylers: [{ color: "#8b949e" }] },
  { elementType: "labels.text.stroke", stylers: [{ color: "#0d1117" }] },
  { featureType: "administrative", elementType: "geometry", stylers: [{ color: "#30363d" }] },
  { featureType: "administrative.country", elementType: "labels.text.fill", stylers: [{ color: "#8b949e" }] },
  { featureType: "road", elementType: "geometry.fill", stylers: [{ color: "#21262d" }] },
  { featureType: "road", elementType: "labels.text.fill", stylers: [{ color: "#8b949e" }] },
  { featureType: "road.highway", elementType: "geometry.fill", stylers: [{ color: "#30363d" }] },
  { featureType: "water", elementType: "geometry", stylers: [{ color: "#010409" }] },
  { featureType: "water", elementType: "labels.text.fill", stylers: [{ color: "#58a6ff" }] }
];

export const RangeMap = ({
  startCoords = { lat: 19.0760, lng: 72.8777 },
  destCoords = null,
  ridingMode = 'eco',
  evRange = 250,
  detourCharger = null,
  routePath = [],
}) => {
  const { googleMapsLoaded, isLeafletFallback } = useMapLoader();
  const parentContainerRef = useRef(null);
  const googleMapRef = useRef(null);
  const leafletMapRef = useRef(null);
  const [activeMapStyle, setActiveMapStyle] = useState('dark');

  // Map instance references
  const gMapInstance = useRef(null);
  const gCircle = useRef(null);
  const gRouteLine = useRef(null);
  const gMarkers = useRef([]);

  const lMapInstance = useRef(null);
  const lCircle = useRef(null);
  const lRouteLine = useRef(null);
  const lMarkers = useRef([]);

  // Resilient distance calculation
  const isReachable = useMemo(() => {
    if (!destCoords) return true;
    const directDist = calculateHaversineDistance(
      startCoords.lat,
      startCoords.lng,
      destCoords.lat,
      destCoords.lng
    );
    return evRange >= directDist;
  }, [startCoords, destCoords, evRange]);

  // ── DUAL RESIZING WITH RESIZEOBSERVER ──
  useEffect(() => {
    if (!parentContainerRef.current) return;

    const handleResize = () => {
      // 1. Google Maps trigger
      if (gMapInstance.current && window.google) {
        window.google.maps.event.trigger(gMapInstance.current, 'resize');
      }
      // 2. Leaflet trigger
      if (lMapInstance.current) {
        lMapInstance.current.invalidateSize();
      }
    };

    const resizeObserver = new ResizeObserver(() => {
      // Debounce slightly to allow dynamic panel/sidebar transitions to finalize
      const timer = setTimeout(handleResize, 100);
      return () => clearTimeout(timer);
    });

    resizeObserver.observe(parentContainerRef.current);

    return () => {
      resizeObserver.disconnect();
    };
  }, [googleMapsLoaded, isLeafletFallback]);

  // ── GOOGLE MAP RENDERING ENGINE ──
  useEffect(() => {
    if (!googleMapsLoaded || isLeafletFallback || !googleMapRef.current) return;

    // Instantiate Google Map only once
    if (!gMapInstance.current) {
      gMapInstance.current = new window.google.maps.Map(googleMapRef.current, {
        center: startCoords,
        zoom: 11,
        styles: activeMapStyle === 'dark' ? DARK_MAP_STYLE : [],
        disableDefaultUI: true,
        zoomControl: true,
      });

      // CRITICAL: Delayed resize trigger to fix fragmented tiles inside animated dashboards
      setTimeout(() => {
        if (gMapInstance.current) {
          window.google.maps.event.trigger(gMapInstance.current, 'resize');
        }
      }, 500);
    }

    const map = gMapInstance.current;
    
    // Dynamically update map theme if toggled
    map.setOptions({ styles: activeMapStyle === 'dark' ? DARK_MAP_STYLE : [] });

    // Cleanup previous markers
    gMarkers.current.forEach((m) => m.setMap(null));
    gMarkers.current = [];

    // Create Start Marker
    const startMarker = new window.google.maps.Marker({
      position: startCoords,
      map: map,
      title: "Start Location",
      icon: {
        path: window.google.maps.SymbolPath.CIRCLE,
        scale: 8,
        fillColor: "#10b981", // Emerald
        fillOpacity: 1,
        strokeColor: "#ffffff",
        strokeWeight: 2,
      }
    });
    gMarkers.current.push(startMarker);

    // Create dynamic Range Circle
    if (gCircle.current) gCircle.current.setMap(null);
    gCircle.current = new window.google.maps.Circle({
      strokeColor: '#10b981',
      strokeOpacity: 0.8,
      strokeWeight: 1.5,
      fillColor: '#10b981',
      fillOpacity: 0.05,
      map: map,
      center: startCoords,
      radius: evRange * 1000, // Range in meters
    });

    // Create Destination and Pathway overlays if specified
    if (destCoords) {
      const destMarker = new window.google.maps.Marker({
        position: destCoords,
        map: map,
        title: "Destination",
        icon: {
          path: window.google.maps.SymbolPath.CIRCLE,
          scale: 8,
          fillColor: isReachable ? "#3b82f6" : "#ef4444", // Blue vs Crimson Red
          fillOpacity: 1,
          strokeColor: "#ffffff",
          strokeWeight: 2,
        }
      });
      gMarkers.current.push(destMarker);

      if (gRouteLine.current) gRouteLine.current.setMap(null);

      // Parse and display route path coordinates
      const parsedPath = parseRoutePath(routePath);
      const finalPath = parsedPath.length > 0 ? parsedPath : [startCoords, destCoords];

      gRouteLine.current = new window.google.maps.Polyline({
        path: finalPath,
        strokeColor: isReachable ? '#10b981' : '#ef4444',
        strokeOpacity: 0.8,
        strokeWeight: 4,
        map: map,
      });

      // Fit bounds cleanly to center both points
      const bounds = new window.google.maps.LatLngBounds();
      bounds.extend(startCoords);
      bounds.extend(destCoords);
      map.fitBounds(bounds);
    } else {
      if (gRouteLine.current) gRouteLine.current.setMap(null);
      map.setCenter(startCoords);
    }
  }, [googleMapsLoaded, isLeafletFallback, startCoords, destCoords, evRange, routePath, activeMapStyle, isReachable]);

  // ── RESILIENT LEAFLET FALLBACK ENGINE ──
  useEffect(() => {
    if (!isLeafletFallback || !leafletMapRef.current || typeof window === 'undefined' || !window.L) return;

    const L = window.L;

    // Instantiate Leaflet Map only once
    if (!lMapInstance.current) {
      lMapInstance.current = L.map(leafletMapRef.current, {
        zoomControl: true,
        attributionControl: false
      }).setView([startCoords.lat, startCoords.lng], 11);

      // Use elegant dark map tiles
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 19
      }).addTo(lMapInstance.current);
    }

    const map = lMapInstance.current;

    // Cleanup previous overlays
    lMarkers.current.forEach((m) => map.removeLayer(m));
    lMarkers.current = [];

    // Create Start Pulse Marker
    const startPulseIcon = L.divIcon({
      className: 'relative flex items-center justify-center',
      html: `<span class="animate-ping absolute inline-flex h-4 w-4 rounded-full bg-emerald-400 opacity-75"></span>
             <span class="relative inline-flex rounded-full h-3.5 w-3.5 bg-emerald-500 border border-white"></span>`,
      iconSize: [16, 16],
      iconAnchor: [8, 8]
    });

    const startMarker = L.marker([startCoords.lat, startCoords.lng], { icon: startPulseIcon }).addTo(map);
    lMarkers.current.push(startMarker);

    // Create dynamic Range Circle
    if (lCircle.current) map.removeLayer(lCircle.current);
    lCircle.current = L.circle([startCoords.lat, startCoords.lng], {
      radius: evRange * 1000,
      color: '#10b981',
      fillColor: '#10b981',
      fillOpacity: 0.05,
      weight: 1.5,
      dashArray: '5, 5'
    }).addTo(map);

    // Create Destination and Route
    if (destCoords) {
      const destPulseIcon = L.divIcon({
        className: 'relative flex items-center justify-center',
        html: `<span class="relative inline-flex rounded-full h-3.5 w-3.5 ${isReachable ? 'bg-blue-500' : 'bg-red-500'} border border-white"></span>`,
        iconSize: [16, 16],
        iconAnchor: [8, 8]
      });

      const destMarker = L.marker([destCoords.lat, destCoords.lng], { icon: destPulseIcon }).addTo(map);
      lMarkers.current.push(destMarker);

      if (lRouteLine.current) map.removeLayer(lRouteLine.current);

      const leafletPath = routePath.length > 0 
        ? routePath.map((pt) => [pt[0], pt[1]]) 
        : [[startCoords.lat, startCoords.lng], [destCoords.lat, destCoords.lng]];

      lRouteLine.current = L.polyline(leafletPath, {
        color: isReachable ? '#10b981' : '#ef4444',
        weight: 4,
        opacity: 0.8,
        dashArray: isReachable ? null : '6, 6'
      }).addTo(map);

      // Fit bounds with comfortable padding
      map.fitBounds(L.latLngBounds([startCoords.lat, startCoords.lng], [destCoords.lat, destCoords.lng]), {
        padding: [40, 40]
      });
    } else {
      if (lRouteLine.current) map.removeLayer(lRouteLine.current);
      map.setView([startCoords.lat, startCoords.lng], 11);
    }
  }, [isLeafletFallback, startCoords, destCoords, evRange, routePath, isReachable]);

  // ── NATIVE UNMOUNT DESTRUCTION & CLEANUP ──
  useEffect(() => {
    return () => {
      // 1. Destroy Google Maps overlay references
      if (gCircle.current) { gCircle.current.setMap(null); gCircle.current = null; }
      if (gRouteLine.current) { gRouteLine.current.setMap(null); gRouteLine.current = null; }
      gMarkers.current.forEach((m) => m.setMap(null));
      gMarkers.current = [];
      gMapInstance.current = null;

      // 2. Safely dismantle Leaflet instance
      if (lMapInstance.current) {
        lMapInstance.current.off();
        lMapInstance.current.remove();
        lMapInstance.current = null;
      }
    };
  }, []);

  return (
    <div
      ref={parentContainerRef}
      className="relative w-full h-[620px] rounded-3xl overflow-hidden border border-slate-800 bg-[#0d1117] shadow-2xl transition-all duration-300"
    >
      {/* Dynamic Style switcher available strictly on Google Maps engine */}
      {googleMapsLoaded && !isLeafletFallback && (
        <div className="absolute top-4 right-4 z-[99] flex gap-1.5 bg-slate-900/90 border border-slate-800 rounded-2xl p-1 backdrop-blur-md">
          <button
            onClick={() => setActiveMapStyle('dark')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-xl transition-all ${
              activeMapStyle === 'dark'
                ? 'bg-emerald-500 text-slate-950 font-bold shadow-lg shadow-emerald-500/25'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            🌌 Cyber Dark
          </button>
          <button
            onClick={() => setActiveMapStyle('light')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-xl transition-all ${
              activeMapStyle === 'light'
                ? 'bg-emerald-500 text-slate-950 font-bold shadow-lg shadow-emerald-500/25'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            🗺️ Google Standard
          </button>
        </div>
      )}

      {/* Cyberpunk Map Styling Overrides */}
      <style>{`
        .gm-style {
          background-color: #0d1117 !important;
        }
        .gm-style iframe + div {
          border: none !important;
        }
        /* Leaflet custom dark theme overlays */
        .leaflet-container {
          background: #0d1117 !important;
        }
      `}</style>

      {/* Exclusivity: Strictly render one engine wrapper DOM tree at a time */}
      <AnimatePresence mode="wait">
        {googleMapsLoaded && !isLeafletFallback ? (
          <motion.div
            key="google-maps-container"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="w-full h-full relative"
          >
            {/* The static, zero-transform mapping viewport container */}
            <div
              ref={googleMapRef}
              className="w-full h-full absolute inset-0 z-10"
              style={{ minHeight: '620px', transform: 'none' }}
            />
          </motion.div>
        ) : (
          <motion.div
            key="leaflet-fallback-container"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="w-full h-full relative"
          >
            {/* The static, zero-transform Leaflet fallback container */}
            <div
              ref={leafletMapRef}
              className="w-full h-full absolute inset-0 z-10"
              style={{ minHeight: '620px', transform: 'none' }}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
