function captureLocation() {
  const statusEl = document.getElementById("location-status");
  const latInput = document.getElementById("latitude");
  const lngInput = document.getElementById("longitude");
  const coordsDisplay = document.getElementById("coords-display");  // new element to show coords

  if (!navigator.geolocation) {
    statusEl.textContent = "Geolocation is not supported by this browser.";
    statusEl.classList.add("text-danger");
    return;
  }

  statusEl.textContent = "Detecting your location...";
  statusEl.classList.remove("text-danger", "text-success");

  navigator.geolocation.getCurrentPosition(
    function (position) {
      const lat = position.coords.latitude;
      const lng = position.coords.longitude;

      latInput.value = lat;
      lngInput.value = lng;

      statusEl.textContent = "Location captured successfully.";
      statusEl.classList.add("text-success");

      // Show latitude and longitude to user for debugging
      if (coordsDisplay) {
        coordsDisplay.textContent = `Latitude: ${lat.toFixed(6)}, Longitude: ${lng.toFixed(6)}`;
      }
    },
    function (error) {
      console.log(error);
      statusEl.textContent = "Unable to get location. Please allow location access or enter another address.";
      statusEl.classList.add("text-danger");
    }
  );
}
