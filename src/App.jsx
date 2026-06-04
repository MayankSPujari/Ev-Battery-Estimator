import { GoogleMap, LoadScript } from '@react-google-maps/api';

const containerStyle = {
  width: '100vw',
  height: '100vh'
};

const center = {
  lat: 12.9716,
  lng: 77.5946
};

export default function App() {
  return (
    <LoadScript
      googleMapsApiKey={import.meta.env.VITE_GOOGLE_MAPS_API_KEY}
      libraries={['places']}
    >
      <GoogleMap
        mapContainerStyle={containerStyle}
        center={center}
        zoom={10}
        onLoad={(map) => {
          setTimeout(() => {
            window.google.maps.event.trigger(map, 'resize');
          }, 500);
        }}
      />
    </LoadScript>
  );
}
