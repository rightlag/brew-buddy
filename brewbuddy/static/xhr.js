var autocomplete;
var input;
function initAutocomplete() {
  input = document.getElementById('autocomplete');
  autocomplete = new google.maps.places.Autocomplete(input);
}
function xhr(event) {
  event.preventDefault();
  // Clear the input field.
  input.value = '';
  var place = autocomplete.getPlace();
  var data = {
    title: place.name,
    lat: place.geometry.location.lat(),
    lng: place.geometry.location.lng()
  };
  var xhttp = $.ajax('/xhr', {
    contentType: 'application/json',
    data: JSON.stringify(data),
    type: 'POST'
  });
  xhttp.done(function (data) {
    var table = document.getElementById('features');
    // By default, assume the item is not found in the array.
    var found = false;
    for (var i = 0; i < table.rows.length; i++) {
      if (data.properties.title === table.rows[i].cells[0].innerHTML) {
        found = true;
        table.rows[i].cells[1].innerHTML++;
        break;
      }
    }
    if (!found) {
      var tbody = table.getElementsByTagName('tbody')[0];
      var row = tbody.insertRow(0);
      var c1 = row.insertCell(0);
      var c2 = row.insertCell(1);
      c1.innerHTML = data.properties.title;
      c1.className = 'mdl-data-table__cell--non-numeric';
      c2.innerHTML = data.properties.description;
    }
  });
  xhttp.fail(function (jqXHR) {
    console.log(jqXHR);
  });
}
