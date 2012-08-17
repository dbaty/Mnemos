function initLiveSearch() {
    $('#live-search').autocomplete({
        source: '/ajax_search',
        minLength: 2,
        select: function(event, ui) {
            window.location = ui.item.url;
            return false;
        }
    }).data('autocomplete')._renderItem = function(ul, item) {
        var link = '<a href="' + item.url + '">' + item.dropdown + '<' + '/a>';
        return $('<li></li>').data('item.autocomplete', item).append(link).appendTo(ul);
    };
}


function showPanel(panel_id) {
    if (typeof current_panel !== undefined) {
        $('#panel-' + current_panel).toggle(false);
    }
    $('#panel-' + panel_id).toggle(true);
    current_panel = panel_id;
}

var map = undefined;

function centerAndZoom(lat, lng, zoom) {
    map.setView(new L.LatLng(lat, lng), zoom);
}


function parseQueryString(str) {
    // Parse the given query string and return an associative array
    // with the key/values of the given hash. We use it here only to
    // parse the hash part of the URL.
    if (!str) {
        return {};
    }
    var values = {};
    var groups = str.split('&');
    for (var i = 0; i < groups.length; i++) {
        var key_value = groups[i].split('=');
        if (!key_value[0].length) {
            continue;
        }
        values[key_value[0]] = key_value[1];
    }
    return values;
}


function initMap() {
    var url = 'http://{s}.tile.cloudmade.com/' +
        leaflet_api_key +
        '/997/256/{z}/{x}/{y}.png';
    map = new L.Map('map');
    var tile_layer = new L.TileLayer(url, {maxZoom: 18});
    map.addLayer(tile_layer);

    // Center on the requested coordinates, or on France if no
    // coordinates have ben given..
    if (window.location.hash) {
        var coord = parseQueryString(window.location.hash.substr(1));
        centerAndZoom(coord.lat, coord.lng, 14);
    } else {
        centerAndZoom(46.830134, 2.764892, 6);
    }

    // Custom icon. In fact, only the URLs is customized.
    var MnemosIcon = L.Icon.extend({
        iconUrl: '/static/img/leaflet/marker.png',
        shadowUrl: '/static/img/leaflet/marker-shadow.png',
        iconSize: new L.Point(25, 41),
        shadowSize: new L.Point(41, 41),
        iconAnchor: new L.Point(13, 41),
        popupAnchor: new L.Point(0, -33)
    });
    var icon = new MnemosIcon();
    var marker_layer = new L.GeoJSON(undefined, {
        pointToLayer: function (latlng) {
            return new L.Marker(latlng, {icon: icon});
        }});

    // Popup when the marker is clicked.
    marker_layer.on('featureparse', function (event) {
        var feat = event.properties;
        var html = '<a href="' + feat.url + '">' + feat.fullname + '</a>';
        if (map.getZoom() < 14) {
            html += ' (<a href="#" onclick="centerAndZoom(' + feat.lat + ',' + feat.lng + ', 14)">' + feat.zoom_in_label + '</a>)';
        }
        event.layer.bindPopup(html);
    });

    // Callback when the user moves the map and new tiles are shown.
    function update_markers() {
        var bbox = map.getBounds().toBBoxString();
        var url = '/contacts-in-bbox?bbox=' + bbox;
        $.getJSON(url, function(data) {
            marker_layer.clearLayers();
            marker_layer.addGeoJSON(data);
            map.addLayer(marker_layer);
        });
    }
    map.on('moveend', update_markers);
    update_markers();
}