var activeTab = null;
var timeago = true;

$.ajax({
	type:"GET",
	url:"/api/config/eventtimeago",
	contentType:"application/json; charset=utf-8",
	dataType:"json",
	data:"{}",
	success:function (res) {
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

function tabs(obj) {
	var str = '<div class="tabbable tabs-left"> <ul id="tabs" class="nav nav-tabs">';
	str += partitions(obj);
	str += zones(obj);
	str += '</ul></div>';

	return str;
}

function details(obj) {
	var str = '';
	str += partitiondetails(obj);
	str += zonedetails(obj);
	return str;
}

function zones(obj) {
	var str = '<li class="nav-header">Zones</li>';
	str += '<li><a href="#zoneall" data-toggle="tab">All</a></li>'
	for (var i = 1; i < 65; i++) {
		var zone = obj.zone[i + ''];
		if (zone) {
			if (zone.name) {
				var cls = zone.status.open ? 'badge-important' : 'badge-success';
				var icon = !zone.status.open ? 'icon-ok-sign' : 'icon-minus-sign';
				var name = obj.zone[i + ''].name;


				str += '<li><a href="#zone' + i + '" data-toggle="tab"> <span class="badge ' + cls + '"> <i class="' + icon + ' icon-white"></i></span>    ' + name + ' </a></li>'
			}
		}
	}

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
				var icon = !zone.status.open ? 'icon-ok-sign' : 'icon-minus-sign';
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
	var str = '<li class="nav-header">Partitions</li>';

	str += '<li><a href="#partitionall" data-toggle="tab">All</a></li>';

	for (var i = 1; i < 65; i++) {
		var partition = obj.partition[i + ''];
		if (partition) {
			if (partition.name) {
				var cls = partition.status.ready ? 'badge-success' : 'badge-important';
				var icon = partition.status.ready ? 'icon-ok-sign' : 'icon-minus-sign';
				var name = obj.partition[i + ''].name;


				str += '<li><a href="#partition' + i + '" data-toggle="tab"> <span class="badge ' + cls + '"> <i class="' + icon + ' icon-white"></i></span>    ' + name + ' </a></li>'
			}
		}
	}

	return str;
}


function partitiondetails(obj) {
	var str = '';
	str += '<div class="tab-pane" id="partitionall">' + createEvents(obj.partition.lastevents) + '</div>';
	for (var i = 1; i < 65; i++) {
		var partition = obj.partition[i + ''];
		if (partition) {
			if (partition.name) {
				var cls = partition.status.ready ? 'badge-success' : 'badge-important';
				var icon = partition.status.ready ? 'icon-ok-sign' : 'icon-minus-sign';
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
		str += '<a class="btn" href="#" onclick="disarm();return false;">Disarm</a>';
	} else if (!exit) {
		str += '<a class="btn" href="#" onclick="doAction(\'arm\');return false;">Arm</a>';
		str += '<a class="btn" href="#" onclick="doAction(\'stayarm\');return false;">Stay</a>';
	}
	if (exit) {
		str += '<a class="btn" href="#" onclick="disarm();return false;">Cancel</a>';
	}

	return str;
}

function disarm() {
	var code = prompt("What is your code?", "");
	$.ajax({
		type:"GET",
		url:"/api/alarm/disarm?code" + code,
		contentType:"application/json; charset=utf-8",
		dataType:"json",
		data:"{}",
		success:function (res) {
			$.scojs_message(res.response, $.scojs_message.TYPE_OK);
		}
	});
}

function doAction(action) {
	$.ajax({
		type:"GET",
		url:"/api/alarm/" + action,
		contentType:"application/json; charset=utf-8",
		dataType:"json",
		data:"{}",
		success:function (res) {
			$.scojs_message(res.response, $.scojs_message.TYPE_OK);
		}
	});
}

function message(obj) {
	var str = '';
	if (obj.partition["1"].status.entry_delay) {
		str += '<span class="label label-info">Entry delay</span>';
	}

	if (obj.partition["1"].status.exit_delay) {
		str += '<span class="label label-info">Exit delay</span>';
	}

	if (obj.partition["1"].status.alarm) {
		str += '<span class="label label-important">Alarm</span>';
	}

	if (obj.partition["1"].status.trouble) {
		str += '<span class="label label-warning">Trouble</span>';
	}

	if (obj.partition["1"].status.tamper) {
		str += '<span class="label label-warning">Tamper</span>';
	}
	$('#message').html(str).fadeIn();
}

function refresh() {
	$.ajax({
		type:"GET",
		url:"/api",
		contentType:"application/json; charset=utf-8",
		dataType:"json",
		data:"{}",
		success:function (res) {
			$('#tabcontainer').html(tabs(res)).fadeIn();
			$('#details').html(details(res)).fadeIn();
			$('#actions').html(actions(res)).fadeIn();
			$('#tabs').tab();

			$('#tabs a[data-toggle="tab"]').on('shown', function (e) {
				activeTab = e.target.hash;
			});
			if (activeTab) {
				$('#tabs a[href="' + activeTab + '"]').tab('show');
			}

			$("[rel=tooltip]").tooltip();

			message(res);
		}
	});
}

$(document).ready(function () {
	refresh();
});


setInterval(function () {
	refresh();
}, 5000);
