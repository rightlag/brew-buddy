(function ($, window, undefined) {
  'use strict';

  var autocomplete;
  var dialog;
  var initial = true;
  var input = document.getElementById('autocomplete');
  var table = document.getElementById('features');
  var loader = document.getElementById('loader');
  loader.style.display = 'none';

  window.onload = function() {
    window.addEventListener('focus', function() {
      input.focus();
    });
    initAutocomplete();
    initTable();
    initDialog();
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
    if (!exists(place, table)) appendRow(place, table);
    updateTable();
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

  function initTable() {
    if (initial) return;
    var tbody = table.getElementsByTagName('tbody')[0];
    var rows = tbody.getElementsByTagName('tr');
    for (var i = 0; i < rows.length; i++) {
      var row = rows[i];
      row.addEventListener('click', showDialog);
    }
  }

  function updateTable() {
    // Add dialog functionality to newly added row.
    var tbody = table.getElementsByTagName('tbody')[0];
    var row = tbody.getElementsByTagName('tr')[0];
    row.addEventListener('click', showDialog);
  }

  function initDialog() {
    dialog = document.getElementById('dialog');
    if (!dialog.showModal) {
      dialogPolyfill.registerDialog(dialog);
    }
    dialog
      .getElementsByClassName('close')[0]
      .addEventListener('click', function() {
        dialog.getElementsByClassName('mdl-dialog__title')[0].innerHTML = '';
        dialog.close();
      });
  }

  function showDialog(event) {
    loader.style.display = 'block';
    document.getElementById('map').style.display = 'none';
    var row = event.srcElement.parentElement;
    var place = {
      properties: {
        title: null
      },
      geometry: {
        coordinates: []
      }
    };
    for (var i = 0; i < row.cells.length; i++) {
      var val = row.cells[i].innerHTML;
      switch(i) {
        case 0:
          place.properties.title = val;
          break;
        case 1:
          continue;
        case 2:
          place.geometry.coordinates.push(parseFloat(val));
          break;
        case 3:
          place.geometry.coordinates.push(parseFloat(val));
          break;
      }
    }
    dialog.getElementsByClassName('mdl-dialog__title')[0].innerHTML = (
      place.properties.title
    );
    dialog.showModal();
    showMap(place);
  }

  function showMap(place) {
    mapboxgl.accessToken = 'pk.eyJ1IjoicmlnaHRsYWciLCJhIjoiY2lwdXN3OXNtMGpscWgybnJmdGN1M3EzcyJ9.yrkKadbWzaE6WX0ygTbGtA';
    var lng = place.geometry.coordinates[0];
    var lat = place.geometry.coordinates[1];
    var map = new mapboxgl.Map({
      container: 'map',
      style: 'mapbox://styles/mapbox/light-v9',
      center: [lng, lat],
      zoom: 12
    });
    var markers = getMarkers(place);
    map.on('load', function() {
      loader.style.display = 'none';
      document.getElementById('map').style.display = 'block';
      map.resize();
      map.addSource('markers', markers);
      map.addLayer({
        id: 'markers',
        type: 'symbol',
        source: 'markers',
        layout: {
          'icon-image': '{marker-symbol}-15',
          'text-field': '{title}',
          'text-font': ['Open Sans Semibold', 'Arial Unicode MS Bold'],
          'text-offset': [0, 0.6],
          'text-anchor': 'top'
        }
      });
    });
  }

  function getMarkers(place) {
    var lng = place.geometry.coordinates[0];
    var lat = place.geometry.coordinates[1];
    var markers = {
      type: 'geojson',
      data: {
        type: 'FeatureCollection',
        features: [{
          type: 'Feature',
          geometry: {
            type: 'Point',
            coordinates: [lng, lat]
          },
          properties: {
            title: place.properties.title,
            'marker-symbol': 'beer'
          }
        }]
      }
    };
    return markers;
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
    var c3 = row.insertCell(2);
    var c4 = row.insertCell(3);
    c1.innerHTML = place.properties.title;
    c1.className = 'mdl-data-table__cell--non-numeric';
    c2.innerHTML = place.properties.description;
    c3.style.display = 'none';
    c3.innerHTML = place.geometry.coordinates[0];
    c4.style.display = 'none';
    c4.innerHTML = place.geometry.coordinates[1];
  }
}(jQuery, window));
