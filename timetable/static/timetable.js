var date = new Date();
var day = date.getDay();
day = (day+6)%7 // Javascript counts from Sunday, Django from Monday
var th_today = document.getElementById("day-"+day);
if (th_today) {
	th_today.scrollIntoView(false);
}

var def_cookie = "timetable_default";
var attributes = "; path=/timetable/; expires=Fri, 31 Dec 9999 23:59:59 GMT";
var def_button = document.getElementById("set-def-button");
function setDefaultTimetable() {
	var path = window.location.pathname;
	document.cookie = def_cookie+"="+path+attributes;
	def_button.style.visibility = "hidden";
}

var clock = document.getElementById("current-time");
function updateClock() {
	clock.textContent = (new Date()).toLocaleTimeString();
}
updateClock();
setInterval(updateClock, 100);

//TODO: fixed left column/table header
