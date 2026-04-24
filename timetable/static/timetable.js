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
weekday = (weekday + 6) % 7;

// Show today's column (for smaller screens)
var th_today = document.getElementById("day-" + weekday);
if (th_today) {
    th_today.scrollIntoView(false);
}
var col_today = document.getElementById("day-" + weekday + "-col");
if (col_today) {
    col_today.className += " highlight"
}

// Constants for the default timetable cookie
var def_cookie = "timetable_default";
var ver_cookie = "timetable_version";
var attributes = "; path=/timetable/; expires=Fri, 31 Dec 9999 23:59:59 GMT";
var def_button = document.getElementById("set-def-button");
var path = window.location.pathname;

// Unhide button if current page isn't default
if (def_button) {
    if (!document.cookie.split(';').filter(function (item) {
        return item.indexOf(def_cookie + "=" + path) >= 0
    }).length) {
        def_button.style.visibility = "visible";
    }
}

// Sets the client's cookie and hides the button
function setDefaultTimetable() {
    document.cookie = def_cookie + "=" + path + attributes;
    if (timetable_version) {
        document.cookie = ver_cookie + "=" + timetable_version + attributes;
    }
    def_button.style.visibility = "hidden";
}

function addMinutes(date, minutes) {
    return new Date(date.getTime() + minutes * 60000);
}

var periods = todays_periods;
var offset = server_utc_offset - (new Date()).getTimezoneOffset();
// FIXME: adjust for timezone difference in a smarter way?
for (var i = 0; i < periods.length; i++) {
    periods[i] = periods[i]['fields'];
    periods[i].begin_time = parseTime(periods[i].begin_time);
    periods[i].begin_time = addMinutes(periods[i].begin_time, offset);
    periods[i].end_time = parseTime(periods[i].end_time);
    periods[i].end_time = addMinutes(periods[i].end_time, offset);
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
    if (periods.length == 0) return;
    if (prev_highlight) {
        prev_highlight.classList.remove("highlight", "break-highlight");
    }
    var timer, until;
    // timer - the <span> element which should be shown
    // until - time to which it is count down

    if (now < periods[0].begin_time) {
        // If it's before all lessons

        // Don't show the clock too early
        if (addMinutes(now, 60) < periods[0].begin_time) {
            return;
        }

        timer = document.getElementById("before-lessons");
        until = periods[0].begin_time;
    } else if (now > periods[periods.length - 1].end_time) {
        // If it's after all lessons
        timer = document.getElementById("after-lessons");
    } else for (var i = 0; i < periods.length; i++) {
        if (periods[i].begin_time < now && now < periods[i].end_time) {
            // If a lesson is ongoing
            timer = document.getElementById("during-lesson");
            var tmp = document.getElementById("period-" + periods[i]['number']);
            if (tmp) {
                var row = tmp.parentElement;
                row.classList.add("highlight");
                prev_highlight = row;
            }
            until = periods[i].end_time;
            let period_no = timer.getElementsByClassName("period-no")[0];
            period_no.textContent = periods[i].number;
            break;
        }
        if (i > 0 && periods[i - 1].end_time < now && now < periods[i].begin_time) {
            // If it's a break between lessons
            timer = document.getElementById("between-lessons");
            var tmp = document.getElementById("period-" + periods[i - 1]['number']);
            if (tmp) {
                var row = tmp.parentElement;
                row.classList.add("break-highlight");
                prev_highlight = row;
            }
            until = periods[i].begin_time;
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
        timer.getElementsByTagName("time")[0].textContent = toDisplay(until - now);
    }
}

function toDisplay(deltaMilliSeconds) {
    // Takes milliseconds and returns a string like minutes:seconds
    var d = deltaMilliSeconds / 1000;
    var minutes = Math.floor(d / 60);
    var seconds = Math.floor(d % 60);
    if (seconds < 10) seconds = '0' + seconds;
    return minutes + ':' + seconds;
}

var lesson_update_interval = 1000;
var lesson_update_expected = 0;

function scheduleLessonUpdate() { // Fixed interval drift correction based on https://stackoverflow.com/questions/18167059
    // Re-schedule using expected timestamps to reduce timer drift.
    var now = Date.now();
    updateLesson();

    if (lesson_update_expected === 0) {
        lesson_update_expected = now + lesson_update_interval;
    } else {
        lesson_update_expected += lesson_update_interval;
        if (lesson_update_expected < now) {
            lesson_update_expected = now + lesson_update_interval;
        }
    }

    var adjusted_interval = lesson_update_expected - Date.now();
    if (adjusted_interval < 0) {
        adjusted_interval = 0;
    }
    setTimeout(scheduleLessonUpdate, adjusted_interval);
}

scheduleLessonUpdate();

// ----- Utilities -----

function _esc(str) {
    // Escapes HTML special chars — use for ALL dynamic content in attributes and text nodes
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function _groupBy(arr, fn) {
    return arr.reduce(function (acc, item) {
        var k = fn(item);
        if (!acc[k]) acc[k] = [];
        acc[k].push(item);
        return acc;
    }, {});
}


// ----- DOM Lookup -----

function _getWeekdayColOffset(weekday) {
    // Returns 0-based index among day columns only (skipping period-number and period-time cols)
    var headers = document.querySelectorAll('#table-wrapper thead th');
    for (var i = 2; i < headers.length; i++) {
        if (headers[i].id === 'day-' + weekday) return i - 2;
    }
    return -1;
}

function _getPeriodRow(period) {
    var td = document.getElementById('period-' + period);
    return td ? td.parentElement : null;
}

function _getLessonCell(period, weekday) {
    var row = _getPeriodRow(period);
    if (!row) return null;
    var col = _getWeekdayColOffset(weekday);
    if (col < 0) return null;
    var tds = row.querySelectorAll('td');
    // tds[0] = period number, tds[1] = period time string, tds[2+] = day columns
    return tds[col + 2] || null;
}

// ----- Lesson HTML Builders -----

function _buildLessonClassMode(lesson) {
    var t = lesson.teacher, s = lesson.subject, r = lesson.room;
    return '<div class="lesson-onerow">' +
        '<a class="teacher" href="/timetable/teacher/' + t.id + '/" title="' + _esc(t.full_name) + '">' + _esc(t.initials) + '</a>' +
        '<span class="subject" title="' + _esc(s.name) + '">' + _esc(s.short_name) + '</span>' +
        '<a class="room" href="/timetable/room/' + r.id + '/" title="' + _esc(r.name) + '">' + _esc(r.short_name) + '</a>' +
        '</div>';
}

var _lessonBuilders = {
    'class': _buildLessonClassMode,
    'group': _buildLessonClassMode,  // same layout as class
};


// ----- Lesson Cell Updates -----

function clearAllLessonCells() {
    var rows = document.querySelectorAll('#table-wrapper tbody tr');
    rows.forEach(function (row) {
        var tds = row.querySelectorAll('td');
        for (var i = 2; i < tds.length; i++) tds[i].innerHTML = '';
    });
}

function updateLessonCell(period, weekday, lessons, mode) {
    var cell = _getLessonCell(period, weekday);
    if (!cell) return;
    var buildFn = _lessonBuilders[mode] || _buildLessonClassMode;
    cell.innerHTML = lessons.map(buildFn).join('');
}

function updateAllLessonCells(lessons, mode) {
    var grouped = _groupBy(lessons, function (l) {
        return l.period + '_' + l.weekday;
    });
    clearAllLessonCells();
    Object.keys(grouped).forEach(function (key) {
        var parts = key.split('_');
        updateLessonCell(parseInt(parts[0]), parseInt(parts[1]), grouped[key], mode);
    });
}


// =====================================================================
// GROUP FILTER (class timetable only)
//
// Reads timetable_init_data (injected by timetable_data.html).
// SSR already shows the correct initial state — JS only handles changes.
// =====================================================================

// Use underscore before the name to indicate "private" module-level variable, not intended for external use

var _groupsFilterData = {
    selectedIds: null,  // Set<Number>
    allGroups: null,  // [{ id, name }]
    allLessons: null,  // full lesson array from init data
};

function initGroupFilter() {
    if (typeof timetable_init_data === 'undefined' || timetable_init_data.type !== 'class') return;

    var data = timetable_init_data;
    _groupsFilterData.allGroups = data.groups;
    _groupsFilterData.allLessons = data.lessons;

    // Initialise selection from URL ?groups=, falling back to what SSR rendered
    var params = new URLSearchParams(window.location.search);
    var urlGroups = params.get('groups');
    if (urlGroups) {
        _groupsFilterData.selectedIds = new Set(urlGroups.split(',').map(Number));
    } else {
        _groupsFilterData.selectedIds = new Set(data.selected_group_ids);
    }

    var filter = document.getElementById('group-filter');
    if (!filter) return;

    // Only show the filter when there are multiple groups to choose from
    if (data.groups.length <= 1) {
        filter.style.display = 'none';
        return;
    }

    _renderGroupCheckboxes();
}

function toggleGroupFilter() {
    var panel = document.getElementById('group-filter-panel');
    if (!panel) return;
    var open = panel.classList.toggle('open');
    var arrow = document.getElementById('group-filter-arrow');
    if (arrow) arrow.innerHTML = open ? '&#9650;' : '&#9660;';
}

function _renderGroupCheckboxes() {
    var panel = document.getElementById('group-filter-panel');
    if (!panel) return;

    var groups = _groupsFilterData.allGroups.slice().sort(function (a, b) {
        return a.name.localeCompare(b.name);
    });

    groups.forEach(function (group) {
        var label = document.createElement('label');

        var cb = document.createElement('input');
        cb.type = 'checkbox';
        cb.checked = _groupsFilterData.selectedIds.has(group.id);
        cb.addEventListener('change', function (e) {
            if (e.target.checked) _groupsFilterData.selectedIds.add(group.id);
            else _groupsFilterData.selectedIds.delete(group.id);
            _applyGroupFilter();
        });

        var span = document.createElement('span');
        span.textContent = ' ' + group.name;

        label.appendChild(cb);
        label.appendChild(span);
        panel.appendChild(label);
    });
}

function _applyGroupFilter() {
    // Re-render only the lesson cells — table skeleton stays intact
    var filtered = _groupsFilterData.allLessons.filter(function (l) {
        return _groupsFilterData.selectedIds.has(l.group.id);
    });
    updateAllLessonCells(filtered, 'class');

    // Toggling "relevant" on substitution rows avoids re-rendering the whole section
    _updateSubstitutionHighlights();

    _syncGroupFilterUrl();
}

function _updateSubstitutionHighlights() {
    var rows = document.querySelectorAll('#substitutions-container tr[data-group-id]');
    rows.forEach(function (row) {
        var gid = parseInt(row.getAttribute('data-group-id'), 10);
        if (_groupsFilterData.selectedIds.has(gid)) row.classList.add('relevant');
        else row.classList.remove('relevant');
    });
}

function _syncGroupFilterUrl() {
    var allSelected = _groupsFilterData.allGroups.every(function (g) {
        return _groupsFilterData.selectedIds.has(g.id);
    });
    var url = new URL(window.location.href);

    if (allSelected || _groupsFilterData.selectedIds.size === 0) {
        url.searchParams.delete('groups');
    } else {
        var sorted = Array.from(_groupsFilterData.selectedIds).sort(function (a, b) {
            return a - b;
        });
        url.searchParams.set('groups', sorted.join(','));
    }
    // Keep commas readable in the address bar
    window.history.replaceState({}, '', url.toString().replace(/%2C/g, ','));
}

initGroupFilter();
