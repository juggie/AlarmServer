var timeago = true;
var expanded = false;
var timerenabled = true;
var timer;

$.ajax({
	type:"GET",
	url:"/api/config/eventtimeago",
	contentType:"application/json; charset=utf-8",
	dataType:"json",
	data:"{}",
	success:function (res) {
		timeago = res.eventtimeago.toLowerCase();
	}
});

function createEvents(list) {
	var str = '';
	str += '<div class="accordion-inner">';

	for (var j = 0; j < list.length; j++) {
		var ev = list[list.length - j - 1];
		var time = ev.datetime;
		var tooltip = jQuery.timeago(ev.datetime);

		str += '<li>' + ev.message + ' ' + '<a href="#" rel="tooltip" data-original-title="' + (timeago ? tooltip : time) + '">' + (timeago ? time : tooltip) + '</a></li>';
	}

	str += '</div>';

	return str;
}

function talllist(obj) {
	var str = '<div class="accordion" id="accordion2">';
	str += partitions(obj);
	str += zones(obj);
	str += '</div>';

	return str;
}

function zones(obj) {
	var str = '<div class="accordion-group"><div class="accordion-heading"><h2><small>Zones</small></h2>';
	for (var i = 1; i < 65; i++) {
		var zone = obj.zone[i + ''];
		if (zone) {
			if (zone.name) {
				var cls = zone.status.open ? 'badge-important' : 'badge-success';
				var icon = !zone.status.open ? 'icon-ok-sign' : 'icon-minus-sign';
				var name = obj.zone[i + ''].name;

				str += '<a div class="accordion-toggle" data-toggle="collapse" data-parent="#accordion2" href="#collapseZone' + i +'"><span class="badge ' + cls + '"> <i class="' + icon + ' icon-white"></i></span>'+ ' ' + name + '</span></a>'

				str += '<div id="collapseZone' + i + '" class="accordion-body collapse">'
				str += createEvents(zone.lastevents);
				str += '</div>';
			}
		}
	}
	str += '</div></div>';
	return str;
}


function partitions(obj) {
	var str = '<div class="accordion-group"><div class="accordion-heading"><h2><small>Partitions</small></h2>';


	for (var i = 1; i < 65; i++) {
		var partition = obj.partition[i + ''];
		if (partition) {
			if (partition.name) {
				var cls = partition.status.ready ? 'badge-success' : 'badge-important';
				var icon = partition.status.ready ? 'icon-ok-sign' : 'icon-minus-sign';
				var name = obj.partition[i + ''].name;

				str += '<a class="accordion-toggle" data-toggle="collapse" data-parent="#accordion2" href="#collapsePart' + i +'"><span class="badge ' + cls + '"> <i class="' + icon + ' icon-white"></i></span>'+ ' ' + name + '</a></span>'

				str += '<div id="collapsePart' + i + '" class="accordion-body collapse">'
        str += createEvents(partition.lastevents);
        str += '</div>';

			}
		}
	}
	str += '</div></div>';
	return str;
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
		str += '<a class="btn" href="#" onclick="disarm();return false;">Cancel</a>';
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
			if(timerenabled) {
				$('#container').html(talllist(res)).fadeIn();
			}
			$('#actions').html(actions(res)).fadeIn();
			$("[rel=tooltip]").tooltip();
		
			if(timerenabled) {	
			//Keep track of what is expanded and what isn't with LocalStorage
			$('.accordion-body').on('hidden', function() {
				if (this.id) {
						localStorage.removeItem(this.id);
						timerenabled = true;
						//console.log('enabling timer');
				}
			}).on('shown', function() {
					if (this.id) {
							localStorage[this.id] = 'true';
							timerenabled = false;
						//	console.log('disabling timer');	
					}
			}).each(function() {
					if (this.id && localStorage[this.id] === 'true' ) {
							$(this).collapse('show');
					}
			});
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

