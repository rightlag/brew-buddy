var autocomplete;
function initAutocomplete() {
  var input = document.getElementById('autocomplete');
  autocomplete = new google.maps.places.Autocomplete(input);
}
function xhr(event) {
  event.preventDefault();
  var place = autocomplete.getPlace();
  var data = {
    name: place.name,
    lat: place.geometry.location.lat(),
    lng: place.geometry.location.lng()
  };
  var xhttp = $.ajax('/xhr', {
    contentType: 'application/json',
    data: JSON.stringify(data),
    type: 'POST'
  });
}
