var date = new Date();
var day = date.getDay();
day = (day+6)%7 // Javascript counts from Sunday, Django from Monday
var th_today = document.getElementById("day-"+day);
th_today.scrollIntoView(false);

var def_cookie = "timetable_default";
var attributes = "; path=/timetable/; expires=Fri, 31 Dec 9999 23:59:59 GMT";
function setDefaultTimetable() {
	var path = window.location.pathname;
	document.cookie = def_cookie+"="+path+attributes;
}

//TODO: fixed left column/table header
