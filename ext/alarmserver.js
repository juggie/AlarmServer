function zones(obj) {
//   console.log(obj);
    var str = '';
    for (var i = 1; i < 65; i++) {
        var zone = obj.zone[i + ''];
        str += '<ul class="unstyled">';
        if (zone) {
            if (zone.name) {
                var cls = zone.status.open ? 'badge-important' : 'badge-success';
                var icon = !zone.status.open ?  'icon-ok-sign' : 'icon-minus-sign';
                var name = obj.zone[i + ''].name;

                var events = '';
                events += '<table class="table table-striped"> <thead> <tr> <th>Message</th> <th>Time</th></tr> </thead> <tbody>';
                for (var j = 0; j < zone.lastevents.length; j++) {
                   events += '<tr> <td>' + zone.lastevents[zone.lastevents.length - j - 1].message + '</td> <td>' + zone.lastevents[zone.lastevents.length - j - 1].datetime + '</td> </tr>'
                }
                events += '</tbody> </table>';
                events = events.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

//                str += '<li><span class="badge ' + cls + '"><i class="' + icon + ' icon-white"></i></span><a href="#" class="btn btn-link" rel="popover" data-placement="right" data-content="' + events + '" data-original-title="Last Events">' + obj.zone[i + ''].name + '</a></li>'
                str += '<li><a href="#" class="badge ' + cls + '" rel="popover" data-placement="right" data-content="' + events + '" data-original-title="' + name + ' Last Events"><i class="' + icon + ' icon-white"></i></a>&nbsp;&nbsp;' + name + '</li>'
            }
        }
        str += '</ul>';
    }

    return str;
}

function partitions(obj) {
    var str = '';
    str += '<ul class="unstyled">';
    for (var i = 1; i < 9; i++) {
        var partition = obj.partition[i + ''];
        if (partition.name) {
            var cls = partition.status.ready ?  'badge-success' : 'badge-important';
            var icon = partition.status.ready ?  'icon-ok-sign' : 'icon-minus-sign';
            var name = obj.zone[i + ''].name;

            var events = '';
            events += '<table class="table table-striped"> <thead> <tr> <th>Message</th> <th>Time</th></tr> </thead> <tbody>';
            for (var j = 0; j < partition.lastevents.length; j++) {
               events += '<tr> <td>' + partition.lastevents[partition.lastevents.length - j - 1].message + '</td> <td>' + partition.lastevents[partition.lastevents.length - j - 1].datetime + '</td> </tr>'
            }
            events += '</tbody> </table>';
            events = events.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

            str += '<li><a href="#" class="badge ' + cls + '" rel="popover" data-placement="right" data-content="' + events + '" data-original-title="' + name + ' Last Events"><i class="' + icon + ' icon-white"></i></a>&nbsp;&nbsp;' + name + '</li>'
        }
    }
    str += '</ul>';

    return str;
}

function actions(obj) {
    var str = '';
    var armed = obj.partition["1"].status.armed;
    var exit = obj.partition["1"].status.exit_delay;

    if (armed) {
//        str += '<div class="btn-group"><a class="btn" href="/api/alarm/disarm">Disarm</a></div>';
        str += '<a id="myLink" class="btn" href="#" onclick="doAction(\'disarm\');return false;">Disarm</a>';
    } else {
        str += '<a id="myLink" class="btn" href="#" onclick="doAction(\'arm\');return false;">Arm</a>';
        str += '<a id="myLink" class="btn" href="#" onclick="doAction(\'stayarm\');return false;">Stay</a>';
    }
    if (exit) {
        str += '<a id="myLink" class="btn" href="#" onclick="doAction(\'disarm\');return false;">Cancel</a>';
    }

    return str;
}

function doAction(action) {
    $.ajax({
        type: "GET",
        url: "/api/alarm/" + action,
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        data: "{}",
        success: function(res) {
            bootbox.alert(res.response, function() {
                refresh();
            });
        }
    });
}

function refresh() {
    $.ajax({
        type: "GET",
        url: "/api",
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        data: "{}",
        success: function(res) {
            $('#zones').html(zones(res)).fadeIn();
            $('#partitions').html(partitions(res)).fadeIn();
            $('#actions').html(actions(res)).fadeIn();
            $("a[rel=popover]").popover({ html : true});
        }
    });
}

$(document).ready(function() {
    refresh();
});


setInterval(function() {
    refresh();
}, 5000);
