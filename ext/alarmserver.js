var activeZone = null;
var activePartition = null;
var timeago = true;

$.ajax({
    type: "GET",
    url: "/api/config/eventtimeago",
    contentType: "application/json; charset=utf-8",
    dataType: "json",
    data: "{}",
    success: function(res) {
    	timeago = res.eventtimeago.toLowerCase() == "true";  
    }
});

function createEvents(list) {
	var str = '';
    str += '<table class="table table-striped table-bordered"> <thead> <tr> <th>Message</th> <th>Time</th></tr> </thead> <tbody>';
               
	for (var j = 0; j < list.length; j++) {
	    var ev = list[list.length - j - 1];
	    var time = ev.datetime;
	    var tooltip = jQuery.timeago(ev.datetime);
	    
	    str += '<tr> <td>' + ev.message + '</td> <td> <a href="#" rel="tooltip" data-placement="top" data-original-title="' + (timeago ? time : tooltip) + '">' + (timeago ? tooltip : time) + '</a></td> </tr>';
	}
	
	str += '</tbody> </table>';
   
	return str;
}

function zones(obj) {
    var str = '<ul id="zonetabs" class="nav nav-list bs-docs-sidenav">';
    str += '<li><a href="#zoneall" data-toggle="tab">All<i class="icon-chevron-right"></i></a></li>'
    
    for (var i = 1; i < 65; i++) {
        var zone = obj.zone[i + ''];
        if (zone) {
            if (zone.name) {
                var cls = zone.status.open ? 'badge-important' : 'badge-success';
                var icon = !zone.status.open ?  'icon-ok-sign' : 'icon-minus-sign';
                var name = obj.zone[i + ''].name;


                str += '<li><a href="#zone' + i + '" data-toggle="tab"> <i class="' + icon + '"></i>    ' + name + ' <i class="icon-chevron-right"></i></a></li>'
            }
        }
    }
    str += '</ul>';

    return str;
}

function zonedetails(obj) {
	var str = '';
	str += '<div class="tab-pane" id="zoneall">' + createEvents(obj.zone.lastevents) + '</div>';
    
    for (var i = 1; i < 65; i++) {
        var zone = obj.zone[i + ''];
        if (zone) {
            if (zone.name) {
                var cls = zone.status.open ? 'badge-important' : 'badge-success';
                var icon = !zone.status.open ?  'icon-ok-sign' : 'icon-minus-sign';
                var name = obj.zone[i + ''].name;

                str += '<div class="tab-pane" id="zone' + i + '">';

                str += createEvents(zone.lastevents);
                str += '</div>';
            }
        }
    }

    return str;

}


function partitions(obj) {
    var str = '<ul id="partitiontabs" class="nav nav-list bs-docs-sidenav">';
    str += '<li><a href="#partitionall" data-toggle="tab">All<i class="icon-chevron-right"></i></a></li>'

    for (var i = 1; i < 65; i++) {
        var partition = obj.partition[i + ''];
        if (partition) {
            if (partition.name) {
                var cls = partition.status.ready ?  'badge-success' : 'badge-important';
                var icon = partition.status.ready ?  'icon-ok-sign' : 'icon-minus-sign';
                var name = obj.partition[i + ''].name;


                str += '<li><a href="#partition' + i + '" data-toggle="tab"> <i class="' + icon + '"></i>    ' + name + ' <i class="icon-chevron-right"></i></a></li>'
            }
        }
    }
    str += '</ul>';

    return str;
}


function partitiondetails(obj) {
    var str = '';
    str += '<div class="tab-pane" id="partitionall">' + createEvents(obj.partition.lastevents) + '</div>';
    for (var i = 1; i < 65; i++) {
        var partition = obj.partition[i + ''];
        if (partition) {
            if (partition.name) {
                var cls = partition.status.ready ?  'badge-success' : 'badge-important';
                var icon = partition.status.ready ?  'icon-ok-sign' : 'icon-minus-sign';
                var name = obj.partition[i + ''].name;

                str += '<div class="tab-pane" id="partition' + i + '">';

                str += createEvents(partition.lastevents);                
                str += '</div>';
            }
        }
    }

    return str;

}


function actions(obj) {
    var str = '';
    var armed = obj.partition["1"].status.armed;
    var exit = obj.partition["1"].status.exit_delay;

    if (armed) {
        str += '<a id="myLink" class="btn" href="#" onclick="disarm();return false;">Disarm</a>';
    } else {
        str += '<a id="myLink" class="btn" href="#" onclick="doAction(\'arm\');return false;">Arm</a>';
        str += '<a id="myLink" class="btn" href="#" onclick="doAction(\'stayarm\');return false;">Stay</a>';
    }
    if (exit) {
        str += '<a id="myLink" class="btn" href="#" onclick="doAction(\'disarm\');return false;">Cancel</a>';
    }

    return str;
}

function disarm() {
    bootbox.prompt("What is your code?", function(result) {
        $.ajax({
            type: "GET",
            url: "/api/alarm/disarm?code" + result,
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            data: "{}",
            success: function(res) {
                bootbox.alert(res.response, function() {
                    refresh();
                });
            }
        });
    });
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
            $('#zonedetails').html(zonedetails(res)).fadeIn();
            $('#partitions').html(partitions(res)).fadeIn();
            $('#partitiondetails').html(partitiondetails(res)).fadeIn();
            $('#actions').html(actions(res)).fadeIn();
            $('#zonetabs').tab();
            $('#partitiondetails').tab();
            $('#zonetabs a[data-toggle="tab"]').on('shown', function (e) {
                activeZone = e.target.hash;
            });
            if (activeZone) {
                $('#zonetabs a[href="' + activeZone + '"]').tab('show');
            }
            $('#partitiontabs a[data-toggle="tab"]').on('shown', function (e) {
                activePartition = e.target.hash;
            });
            if (activePartition) {
                $('#partitiontabs a[href="' + activePartition + '"]').tab('show');
            }
            $("[rel=tooltip]").tooltip();
        }
    });
}

$(document).ready(function() {
    refresh();
});


setInterval(function() {
    refresh();
}, 5000);
