(function () {
  'use strict';

  var autocomplete;
  var initial = true;
  var input = document.getElementById('autocomplete');

  window.onload = function() {
    initAutocomplete();
  };

  function initAutocomplete() {
    var options = {
      type: [
        'bar',
        'liquor_store',
        'meal_delivery',
        'meal_takeaway',
        'night_club',
        'restaurant'
      ]
    };
    autocomplete = new google.maps.places.Autocomplete(input, options);
    autocomplete.addListener('place_changed', persistPlace);
  }

  function persistPlace() {
    input.value = '';

    var place = autocomplete.getPlace();
    if (!place.geometry) return;
    persist(place).then(done, fail);
  }

  function done(place) {
    var table = document.getElementById('features');
    if (!exists(place, table)) appendRow(place, table);
  }

  function fail(jqXHR) {
    if (jqXHR.status === 404) return;
  }

  function persist(place) {
    var data = {
      title: place.name,
      lat: place.geometry.location.lat(),
      lng: place.geometry.location.lng()
    };
    var settings = {
      contentType: 'application/json',
      data: JSON.stringify(data),
      type: 'POST'
    };
    var jqXHR = $.ajax('/persist', settings);
    return jqXHR;
  }

  function exists(place, table) {
    for (var i = 0; i < table.rows.length; i++) {
      if (place.properties.title === table.rows[i].cells[0].innerHTML) {
        table.rows[i].cells[1].innerHTML++;
        return true;
      }
    }
    return false;
  }

  function appendRow(place, table) {
    var tbody = table.getElementsByTagName('tbody')[0];
    var isFirst = tbody.rows.length < 2;
    if (isFirst && initial) {
      initial = false;
      tbody.deleteRow(0);
    }
    var row = tbody.insertRow(0);
    var c1 = row.insertCell(0);
    var c2 = row.insertCell(1);
    c1.innerHTML = place.properties.title;
    c1.className = 'mdl-data-table__cell--non-numeric';
    c2.innerHTML = place.properties.description;
  }
}());
