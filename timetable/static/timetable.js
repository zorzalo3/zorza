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

var date = new Date();
var weekday = date.getDay();
// Javascript counts from Sunday, Python (Django) from Monday
weekday = (weekday+6)%7;

// Show today's column (for smaller screens)
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
var path = window.location.pathname;

// Unhide button if current page isn't default
if (def_button) {
	if (!document.cookie.split(';').filter(function(item) {
		return item.indexOf(def_cookie+"="+path) >= 0
	}).length) {
		def_button.style.visibility = "visible";
	}
}

// Sets the client's cookie and hides the button
function setDefaultTimetable() {
	document.cookie = def_cookie+"="+path+attributes;
	def_button.style.visibility = "hidden";
}

function addMinutes(date, minutes) {
    return new Date(date.getTime() + minutes*60000);
}

var periods = todays_periods;
var offset = server_utc_offset - (new Date()).getTimezoneOffset();
// FIXME: adjust for timezone difference in a smarter way?
for (var i = 0; i < periods.length; i++) {
	periods[i] = periods[i]['fields'];
	periods[i]['begin_time'] = parseTime(periods[i]['begin_time']);
	periods[i]['begin_time'] = addMinutes(periods[i]['begin_time'], offset);
	periods[i]['end_time'] = parseTime(periods[i]['end_time']);
	periods[i]['end_time'] = addMinutes(periods[i]['end_time'], offset);
}

function parseTime(string) {
	var date = new Date(),
		parts = string.split(':');
	date.setHours(+parts[0]);
	date.setMinutes(+parts[1]);
	date.setSeconds(0);
	date.setMilliseconds(0);
	return date;
}

var prev_highlight, prev_timer;
// Previously shown elements for easy resetting

function updateLesson() {
	var now = new Date();
	let clock = document.getElementById("display-time");
	if (clock) {
		clock.textContent = now.toLocaleTimeString();
	}
	if (!periods) return;
	if (prev_highlight) {
		prev_highlight.classList.remove("highlight", "break-highlight");
	}
	var timer, until;
	// timer - the <span> element which should be shown
	// until - time to which it is count down

	if (now < periods[0]['begin_time']) {
		// If it's before all lessons

		// Don't show the clock too early
		if (addMinutes(now, 60) < periods[0]['begin_time']) {
			return;
		}

		timer = document.getElementById("before-lessons");
		until = periods[0]['begin_time'];
	} else if (now > periods[periods.length-1]['end_time']) {
		// If it's after all lessons
		timer = document.getElementById("after-lessons");
	} else for (var i = 0; i < periods.length; i++) {
		if (periods[i]['begin_time'] < now && now < periods[i]['end_time']) {
			// If a lesson is ongoing
			timer = document.getElementById("during-lesson");
			var tmp = document.getElementById("period-"+periods[i]['number']);
			if (tmp) {
				var row = tmp.parentElement;
				row.classList.add("highlight");
				prev_highlight = row;
			}
			until = periods[i]['end_time'];
			let period_no = timer.getElementsByClassName("period-no")[0];
			period_no.textContent = periods[i].number;
			break;
		}
		if (i > 0 && periods[i-1]['end_time'] < now && now < periods[i]['begin_time']) {
			// If it's a break between lessons
			timer = document.getElementById("between-lessons");
			var tmp = document.getElementById("period-"+periods[i-1]['number']);
			if (tmp) {
				var row = tmp.parentElement;
				row.classList.add("break-highlight");
				prev_highlight = row;
			}
			until = periods[i]['begin_time'];
			let period_no = timer.getElementsByClassName("period-no")[0];
			period_no.textContent = periods[i].number;
			break;
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
	// Takes milliseconds and returns a string like minutes:seconds
	var d = deltaMilliSeconds / 1000;
	var minutes = Math.floor(d/60);
	var seconds = Math.floor(d%60);
	if (seconds < 10) seconds = '0'+seconds;
	return minutes + ':' + seconds;
}

updateLesson();
setInterval(updateLesson, 1000);
// FIXME: setInterval can drift and we can skip seconds as a result
