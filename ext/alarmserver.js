var activeTab = null;
var activeCollapse = null;
var timeago = true;
var autorefresh = true;
var cache = {};

window.matchMediaPhone = function () {
	return matchMedia('(max-width: 767px)').matches;
}
window.matchMediaTablet = function () {
	return matchMedia('(min-width: 768px) and (max-width: 979px)').matches;
}
window.matchMediaDesktop = function () {
	return matchMedia('(min-width: 979px)').matches;
}

$.ajax({
	type: "GET",
	url: "/api/config/eventtimeago",
	contentType: "application/json; charset=utf-8",
	dataType: "json",
	data: "{}",
	success: function (res) {
		timeago = res.eventtimeago.toLowerCase() == "true";
	}
});

function createEvents(list) {
	var source = $("#events-template").html();
	var template = Handlebars.compile(source);

	list.reverse().forEach(function (ev, i) {
		ev.time = moment(ev.datetime).calendar();
	});

	return template({events: list, timeago: timeago});
}

function details(obj, templateId) {
	var source = $(templateId).html();
	var template = Handlebars.compile(source);

	var zones = [];
	for (var i = 1; i < 65; i++) {
		var zone = obj.zone[i + ''];
		if (zone && zone.name) {
			zone.id = i;
			zone.class = zone.status.open ? 'badge-important' : 'badge-success';
			zone.icon = !zone.status.open ? 'icon-ok-sign' : 'icon-minus-sign';
			zone.events = createEvents(zone.lastevents);
			zone.selected = "";
			if (activeCollapse == "collapseZone" + i) {
				zone.selected = "in";
			}
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
			partition.selected = "";
			if (activeCollapse == "collapsePart" + i) {
				partition.selected = "in";
			}
			partitions.push(partition);
		}
	}

	return template({zones: zones,
		zoneAllEvents: createEvents(obj.zone.lastevents),
		partitions: partitions,
		partitionAllEvents: createEvents(obj.partition.lastevents),
		zoneAllSelected: activeCollapse == "collapseZoneAll" ? "in" : "",
		partitionAllSelected: activeCollapse == "collapsePartAll" ? "in" : "",
	});
}

function actions(obj) {
	var source = $("#actions-template").html();
	var template = Handlebars.compile(source);

	return template({
		arm: !obj.partition["1"].status.armed && !obj.partition["1"].status.exit_delay,
		disarm: obj.partition["1"].status.armed,
		cancel: obj.partition["1"].status.exit_delay,
		pgm: obj.partition["1"].status.pgm_output
	});
}

function disarm() {
	alertify.prompt("What is your code?", function (e, code) {
		if (e) {
			doAction("/api/alarm/disarm?alarmcode=" + code);
		}
	});
}

function pgm() {
	alertify.prompt("Enter PGM # to trigger", function (e, pgmnum) {
		if (e) {
			alertify.prompt("What is your code?", function (e1, code) {
				if (e1) {
					doAction("/api/pgm?pgmnum=" + pgmnum + "&alarmcode=" + code);
			 	}
			});
	    }
	});
}

function armwithcode() {
	alertify.prompt("What is your code?", function (e, code) {
		if (e) {
			console.log(code);
			doAction("/api/alarm/armwithcode?alarmcode=" + code);
	    } else {
	    	alertify.error("not armed")
	    }
	});
}

function doAction(action) {
	console.log(action);
	$.ajax({
		type: "GET",
		url: action,
		contentType: "application/json; charset=utf-8",
		dataType: "json",
		success: function (res) {
			console.log(res.response);
			alertify.success(res.response);
		},
		error: function () {
			alertify.error("error performing action");
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

function update(id, value, force) {
	var old = cache[id];
	if (old != value || force) {
		$(id).html(value).fadeIn();
		cache[id] = value;
		return true;
	}
	return false;
}

function refresh(force) {
	$.ajax({
		type: "GET",
		url: "/api",
		contentType: "application/json; charset=utf-8",
		dataType: "json",
		data: "{}",
		success: function (res) {
			if (matchMediaPhone()) {
				update('#mobile-details', details(res, "#mobile-template"), force);
			} else {
				if (update('#details', details(res, "#template")), force) {
					if (activeTab) {
						$('#tabs a[href="' + activeTab + '"]').tab('show');
					}
				}
			}
			update('#actions', actions(res), force);
			$('#tabs').tab();

			$('#tabs a[data-toggle="tab"]').on('shown', function (e) {
				activeTab = e.target.hash;
			});
			$('.accordion-body').on('show',function () {
				activeCollapse = this.id;
			}).on('hide', function () {
					activeCollapse = null;
				});

			if (autorefresh) {
				$("#autorefresh").addClass('active');
			}

			if (timeago) {
				$("#timeago").addClass('active');
			}

			message(res);
		}
	});
}

$(document).ready(function () {
	refresh();
	FastClick.attach(document.body);
});


setInterval(function () {
	if (autorefresh) {
		refresh(false);
	}
}, 5000);
