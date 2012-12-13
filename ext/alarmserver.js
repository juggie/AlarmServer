function zones(obj) {
//   console.log(obj);
    var str = '';
    for (var i = 1; i < 65; i++) {
        var zone = obj.zone[i + ''];
        if (zone.name) {
            str += '<li>' + obj.zone[i + ''].name + ' ' + zone.status.open + '</li>';
        }
    }

    return str;
}

function partitions(obj) {
//   console.log(obj);
    var str = '';
    for (var i = 1; i < 9; i++) {
        var partition = obj.partition[i + ''];
        if (partition.name) {
            str += '<li>' + obj.partition[i + ''].name + ' ready: ' + partition.status.ready + ' armed: ' + partition.status.armed + '</li>';
        }
    }

    return str;
}

function callApi() {
    $.ajax({
        type: "GET",
        url: "/api",
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        data: "{}",
        success: function(res) {
            $('#zones').html(zones(res)).fadeIn();
            $('#partitions').html(partitions(res)).fadeIn();
        }
    });
}

$(document).ready(function() {
    callApi();
});

setInterval(function() {
    callApi();
}, 5000);
