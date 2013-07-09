var activeTab = null;
var activeCollapse = null;
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
	var source  = $("#events-template").html();
	var template = Handlebars.compile(source);

	list.reverse().forEach(function (ev, i) {
		if (timeago) {
			ev.tooltip = ev.datetime;
			ev.time = jQuery.timeago(ev.datetime);
		} else {
			ev.tooltip = jQuery.timeago(ev.datetime);
			ev.time = ev.datetime;
		}
	});

	return template({events: list});
}

function details(obj, templateId) {
	var source  = $(templateId).html();
	var template = Handlebars.compile(source);

	var zones = [];
	for (var i = 1; i < 65; i++) {
		var zone = obj.zone[i + ''];
		if (zone && zone.name) {
			zone.id = i;
			zone.class = zone.status.open ? 'badge-important' : 'badge-success';
			zone.icon = !zone.status.open ? 'icon-ok-sign' : 'icon-minus-sign';
			zone.events = createEvents(zone.lastevents);
			zones.push(zone);
		}
	}

	var partitions = [];
	for (var i = 1; i < 65; i++) {
		var partition = obj.partition[i + ''];
		if (partition && partition.name) {
			partition.id = i;
			partition.class = partition.status.ready ? 'badge-success' : 'badge-important';
			partition.icon = partition.status.ready ? 'icon-ok-sign' : 'icon-minus-sign';
			partition.events = createEvents(partition.lastevents);
			partitions.push(partition);
		}
	}

	return template({zones: zones, zoneAllEvents: createEvents(obj.zone.lastevents), partitions: partitions, partitionAllEvents: createEvents(obj.partition.lastevents)});
}

function actions(obj) {
	var str = '';
	var armed = obj.partition["1"].status.armed;
	var exit = obj.partition["1"].status.exit_delay;
	var pgm_output = obj.partition["1"].status.pgm_output;

	if (armed) {
		str += '<a class="btn" href="#" onclick="disarm();return false;">Disarm</a>';
	} else if (pgm_output) {
		/* Dont show any button, you can't cancel a PGM output */
		str += '';
        } else if (!exit) {
                /* Quick arm is default now with new drop down to select Arm with code */
                str += '<div class="btn-group">';
                str += '<button class="btn"><a href="#" onclick="doAction(\'arm\');return false;">Quick Arm</a></button>';
                str += '<button class="btn dropdown-toggle" data-toggle="dropdown">';
                str += '<span class="caret"></span></button><ul class="dropdown-menu">';
		str += '<li><a href="#" onclick="armwithcode();return false;">Arm W/Code</a></li>';
                str += '</ul></div>';
                /* Now back to regular buttons here */
		str += '<a class="btn" href="#" onclick="doAction(\'stayarm\');return false;">Stay</a> ';
		str += '<a class="btn" href="#" onclick="pgm();return false;">PGM</a> ';
	}
	if (exit) {
		str += '<a class="btn-small" href="#" onclick="disarm();return false;">Cancel</a>';
	}

	return str;
}

function disarm() {
	var code = prompt("What is your code?", "");
	$.ajax({
		type:"GET",
		url:"/api/alarm/disarm?alarmcode=" + code,
		contentType:"application/json; charset=utf-8",
		dataType:"json",
		data:"{}",
		success:function (res) {
			$.scojs_message(res.response, $.scojs_message.TYPE_OK);
		}
	});
}

function pgm() {
	var pgmnum= prompt("Enter PGM # to trigger", "");
	var code= prompt("What is your code?", "");
	$.ajax({
		type:"GET",
		url:"/api/pgm?pgmnum=" + pgmnum + "&alarmcode=" + code,
		contentType:"application/json; charset=utf-8",
		dataType:"json",
		data:"{}",
		success:function (res) {
			$.scojs_message(res.response, $.scojs_message.TYPE_OK);
		}
	});
}

function armwithcode() {
	var code = prompt("What is your code?", "");
	$.ajax({
		type:"GET",
		url:"/api/alarm/armwithcode?alarmcode=" + code,
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

	if (obj.partition["1"].status.pgm_output) {
		str += '<span class="label label-info">PGM Output in progress</span>';
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
			$('#details').html(details(res, "#template")).fadeIn();
			$('#mobile-details').html(details(res, "#mobile-template")).fadeIn();
			$('#actions').html(actions(res)).fadeIn();
			$('#tabs').tab();

			$('#tabs a[data-toggle="tab"]').on('shown', function (e) {
				activeTab = e.target.hash;
			});
			if (activeTab) {
				$('#tabs a[href="' + activeTab + '"]').tab('show');
			}

			$("[rel=tooltip]").tooltip();

			$('.accordion-body').on('shown', function() {
				activeCollapse = this.id;
				console.log(activeCollapse);
			}).on('hidden', function() {
				activeCollapse = null;
			});
			if (activeCollapse) {
				$('#accordion2 #' + activeCollapse).collapse('show');
			}

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
