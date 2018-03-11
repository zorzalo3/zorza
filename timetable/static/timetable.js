"use strict";

// Show today's column (for smaller screens)
var date = new Date();
var weekday = date.getDay();
// Javascript counts from Sunday, Python (Django) from Monday
weekday = (weekday+6)%7;
var th_today = document.getElementById("day-"+weekday);
if (th_today) {
	th_today.scrollIntoView(false);
}
var col_today = document.getElementById("day-"+weekday+"-col");
if (col_today) {
	col_today.className += " highlight"
}

// Constants for the default timetable cookie
var def_cookie = "timetable_default";
var attributes = "; path=/timetable/; expires=Fri, 31 Dec 9999 23:59:59 GMT";
var def_button = document.getElementById("set-def-button");

// Sets the client's cookie and hides the button
function setDefaultTimetable() {
	var path = window.location.pathname;
	document.cookie = def_cookie+"="+path+attributes;
	def_button.style.visibility = "hidden";
}

// Show the correct time
var clock = document.getElementById("current-time");
function updateClock() {
	clock.textContent = (new Date()).toLocaleTimeString();
}
updateClock();
setInterval(updateClock, 100);

var periods = todays_periods;
for (var i = 0; i < periods.length; i++) {
	periods[i] = periods[i]['fields'];
	periods[i]['begin_time'] = parseTime(periods[i]['begin_time']);
	periods[i]['end_time'] = parseTime(periods[i]['end_time']);
}

function parseTime(string) {
	var date = new Date(),
		parts = string.split(':');
	date.setHours(+parts[0]);
	date.setMinutes(+parts[1]);
	date.setSeconds(0);
	return date;
}

var prev_highlight;
function updateLesson() {
	var now = new Date();
	if (prev_highlight)
		prev_highlight.classList.remove("highlight");
	for (var i = 0; i < periods.length; i++) {
		if (periods[i]['begin_time'] < now && now < periods[i]['end_time']) {
			var row = document.getElementById("period-"+periods[i]['number']).parentElement;
			row.className += " highlight";
			prev_highlight = row;
			break;
		}
	}
}

updateLesson();
setInterval(updateLesson, 500);
