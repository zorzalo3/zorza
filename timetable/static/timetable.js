"use strict";
/*
 *
 * @licstart  The following is the entire license notice for the
 *  JavaScript code in this page.
 *
 * Copyright (C) 2018  Wiktor Kuchta
 *
 * The JavaScript code in this page is free software: you can
 * redistribute it and/or modify it under the terms of the GNU
 * General Public License (GNU GPL) as published by the Free Software
 * Foundation, either version 3 of the License, or (at your option)
 * any later version.  The code is distributed WITHOUT ANY WARRANTY;
 * without even the implied warranty of MERCHANTABILITY or FITNESS
 * FOR A PARTICULAR PURPOSE.  See the GNU GPL for more details.
 *
 * As additional permission under GNU GPL version 3 section 7, you
 * may distribute non-source (e.g., minimized or compacted) forms of
 * that code without the copy of the GNU GPL normally required by
 * section 4, provided you include this license notice and a URL
 * through which recipients can access the Corresponding Source.
 *
 * @licend  The above is the entire license notice
 * for the JavaScript code in this page.
 *
 */

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

var prev_highlight, prev_timer;
function updateLesson() {
	var now = new Date();
	if (prev_highlight)
		prev_highlight.classList.remove("highlight");
	var timer, until;
	if (now < periods[0]['begin_time']) {
		timer = document.getElementById("before-lessons");
		until = periods[0]['begin_time'];
	} else if (now > periods[periods.length-1]['end_time']) {
		timer = document.getElementById("after-lessons");
	} else for (var i = 0; i < periods.length; i++) {
		if (periods[i]['begin_time'] < now && now < periods[i]['end_time']) {
			// If a lesson is ongoing
			var row = document.getElementById("period-"+periods[i]['number']).parentElement;
			row.className += " highlight";
			prev_highlight = row;
			timer = document.getElementById("during-lesson");
			until = periods[i]['end_time'];
			break;
		}
		if (i > 0 && periods[i-1]['end_time'] < now && now < periods[i]['begin_time']) {
			timer = document.getElementById("between-lessons");
			until = periods[i]['begin_time'];
		}
	}
	if (prev_timer)
		prev_timer.setAttribute("hidden", "true");
	prev_timer = timer;
	timer.removeAttribute("hidden");
	if (until) {
		timer.getElementsByTagName("time")[0].textContent = toDisplay(until-now);
	}
}

function toDisplay(deltaMilliSeconds) {
	var d = deltaMilliSeconds / 1000;
	var minutes = Math.floor(d/60);
	var seconds = Math.floor(d%60);
	if (seconds < 10) seconds = '0'+seconds;
	return minutes + ':' + seconds;
}

if (periods.length) {
	updateLesson();
	setInterval(updateLesson, 500);
}
