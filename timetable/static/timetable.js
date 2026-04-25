"use strict";

let currentDate = new Date();
let currentWeekday = currentDate.getDay();
currentWeekday = (currentWeekday + 6) % 7;

let tableHeaderToday = document.getElementById("day-" + currentWeekday);
if (tableHeaderToday) {
    tableHeaderToday.scrollIntoView(false);
}

let todayColumn = document.getElementById("day-" + currentWeekday + "-col");
if (todayColumn) {
    todayColumn.className += " highlight";
}

const defaultCookieKey = "timetable_default";
const cookieVersionKey = "timetable_version";
const cookieAttributes = "; path=/timetable/; expires=Fri, 31 Dec 9999 23:59:59 GMT";
let defaultButton = document.getElementById("set-def-button");
let currentPath = window.location.pathname + window.location.search;

if (defaultButton) {
    if (!document.cookie.split(';').filter(item => item.indexOf(defaultCookieKey + "=" + currentPath) >= 0).length) {
        defaultButton.style.visibility = "visible";
    }
}

function setDefaultTimetable() {
    document.cookie = defaultCookieKey + "=" + currentPath + cookieAttributes;
    if (typeof timetable_version !== 'undefined') {
        document.cookie = cookieVersionKey + "=" + timetable_version + cookieAttributes;
    }
    defaultButton.style.visibility = "hidden";
}

function addMinutes(date, minutes) {
    return new Date(date.getTime() + minutes * 60000);
}

let periods = todays_periods;
const offset = server_utc_offset - (new Date()).getTimezoneOffset();
for (let i = 0; i < periods.length; i++) {
    periods[i] = periods[i]['fields'];
    periods[i].beginTime = parseTime(periods[i].begin_time);
    periods[i].beginTime = addMinutes(periods[i].beginTime, offset);
    periods[i].endTime = parseTime(periods[i].end_time);
    periods[i].endTime = addMinutes(periods[i].endTime, offset);
}

function parseTime(string) {
    let date = new Date();
    let parts = string.split(':');
    date.setHours(+parts[0]);
    date.setMinutes(+parts[1]);
    date.setSeconds(0);
    date.setMilliseconds(0);
    return date;
}

let prevHighlight, prevTimer;

function updateLesson() {
    let now = new Date();
    let clockElement = document.getElementById("display-time");
    if (clockElement) {
        clockElement.textContent = now.toLocaleTimeString();
    }
    if (periods.length === 0) return;
    if (prevHighlight) {
        prevHighlight.classList.remove("highlight", "break-highlight");
    }
    var timer, until;
    // timer - the <span> element which should be shown
    // until - time to which it is count down

    if (now < periods[0].begin_time) {
        // If it's before all lessons

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
                prevHighlight = row;
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
                prevHighlight = row;
            }
            until = periods[i].begin_time;
            let period_no = timer.getElementsByClassName("period-no")[0];
            period_no.textContent = periods[i].number;
            break;
        }
    }
    if (prevTimer) prevTimer.setAttribute("hidden", "true");
    prevTimer = timerElement;
    if (timerElement) {
        timerElement.removeAttribute("hidden");
        if (countdownUntil) {
            timerElement.getElementsByTagName("time")[0].textContent = toDisplay(countdownUntil - now);
        }
    }
}

function toDisplay(deltaMilliseconds) {
    let d = deltaMilliseconds / 1000;
    let minutes = Math.floor(d / 60);
    let seconds = Math.floor(d % 60);
    if (seconds < 10) seconds = '0' + seconds;
    return minutes + ':' + seconds;
}

const lessonUpdateInterval = 1000;
let lessonUpdateExpected = 0;

function scheduleLessonUpdate() {
    let now = Date.now();
    updateLesson();

    if (lessonUpdateExpected === 0) {
        lessonUpdateExpected = now + lessonUpdateInterval;
    } else {
        lessonUpdateExpected += lessonUpdateInterval;
        if (lessonUpdateExpected < now) {
            lessonUpdateExpected = now + lessonUpdateInterval;
        }
    }

    let adjustedInterval = lessonUpdateExpected - Date.now();
    if (adjustedInterval < 0) {
        adjustedInterval = 0;
    }
    setTimeout(scheduleLessonUpdate, adjustedInterval);
}

scheduleLessonUpdate();

// ----- Utilities -----

function esc(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function groupBy(arr, fn) {
    return arr.reduce(function (acc, item) {
        let k = fn(item);
        if (!acc[k]) acc[k] = [];
        acc[k].push(item);
        return acc;
    }, {});
}


// ----- DOM Lookup -----

function getWeekdayColOffset(weekday) {
    let headers = document.querySelectorAll('#table-wrapper thead th');
    for (let i = 2; i < headers.length; i++) {
        if (headers[i].id === 'day-' + weekday) return i - 2;
    }
    return -1;
}

function getPeriodRow(period) {
    let td = document.getElementById('period-' + period);
    return td ? td.parentElement : null;
}

function getLessonCell(period, weekday) {
    let row = getPeriodRow(period);
    if (!row) return null;
    let col = getWeekdayColOffset(weekday);
    if (col < 0) return null;
    let tds = row.querySelectorAll('td');
    return tds[col + 2] || null;
}

// ----- Lesson HTML Builders -----

function buildLessonClassMode(lesson) {
    let t = lesson.teacher, s = lesson.subject, r = lesson.room;
    return '<div class="lesson-onerow">' +
        '<a class="teacher" href="/timetable/teacher/' + t.id + '/" title="' + esc(t.full_name) + '">' + esc(t.initials) + '</a>' +
        '<span class="subject" title="' + esc(s.name) + '">' + esc(s.short_name) + '</span>' +
        '<a class="room" href="/timetable/room/' + r.id + '/" title="' + esc(r.name) + '">' + esc(r.short_name) + '</a>' +
        '</div>';
}

const lessonBuilders = {
    'class': buildLessonClassMode,
    'group': buildLessonClassMode,  // same layout as class
};


// ----- Lesson Cell Updates -----

function clearAllLessonCells() {
    let rows = document.querySelectorAll('#table-wrapper tbody tr');
    rows.forEach(function (row) {
        let tds = row.querySelectorAll('td');
        for (let i = 2; i < tds.length; i++) tds[i].innerHTML = '';
    });
}

function updateLessonCell(period, weekday, lessons, mode) {
    let cell = getLessonCell(period, weekday);
    if (!cell) return;
    let buildFn = lessonBuilders[mode] || buildLessonClassMode;
    cell.innerHTML = lessons.map(buildFn).join('');
}

function updateAllLessonCells(lessons, mode) {
    let grouped = groupBy(lessons, function (l) {
        return l.period + '_' + l.weekday;
    });
    clearAllLessonCells();
    Object.keys(grouped).forEach(function (key) {
        let parts = key.split('_');
        updateLessonCell(parseInt(parts[0]), parseInt(parts[1]), grouped[key], mode);
    });
}


// =====================================================================
// GROUP FILTER (class timetable only)
//
// Reads timetable_init_data (injected by timetable_data.html).
// SSR already shows the correct initial state — JS only handles changes.
// =====================================================================

const groupsFilterData = {
    selectedIds: null,  // Set<Number>
    allGroups: null,  // [{ id, name }]
    allLessons: null,  // full lesson array from init data
};

function initGroupFilter() {
    if (typeof timetable_init_data === 'undefined' || timetable_init_data.type !== 'class') return;

    let data = timetable_init_data;
    groupsFilterData.allGroups = data.groups;
    groupsFilterData.allLessons = data.lessons;

    // Initialise selection from URL ?groups=, falling back to what SSR rendered
    let params = new URLSearchParams(window.location.search);
    let urlGroups = params.get('groups');
    if (urlGroups) {
        groupsFilterData.selectedIds = new Set(urlGroups.split(',').map(Number));
    } else {
        groupsFilterData.selectedIds = new Set(data.selected_group_ids);
    }

    let filter = document.getElementById('group-filter');
    if (!filter) return;

    // Only show the filter when there are multiple groups to choose from
    if (data.groups.length <= 1) {
        filter.style.display = 'none';
        return;
    }

    renderGroupCheckboxes();
}

function toggleGroupFilter() {
    let panel = document.getElementById('group-filter-panel');
    if (!panel) return;
    let open = panel.classList.toggle('open');
    let arrow = document.getElementById('group-filter-arrow');
    if (arrow) arrow.innerHTML = open ? '&#9650;' : '&#9660;';
}

function renderGroupCheckboxes() {
    let panel = document.getElementById('group-filter-panel');
    if (!panel) return;

    let groups = groupsFilterData.allGroups.slice().sort(function (a, b) {
        return a.name.localeCompare(b.name);
    });

    groups.forEach(function (group) {
        let label = document.createElement('label');

        let cb = document.createElement('input');
        cb.type = 'checkbox';
        cb.checked = groupsFilterData.selectedIds.has(group.id);
        cb.addEventListener('change', function (e) {
            if (e.target.checked) groupsFilterData.selectedIds.add(group.id);
            else groupsFilterData.selectedIds.delete(group.id);
            applyGroupFilter();
        });

        let span = document.createElement('span');
        span.textContent = ' ' + group.name;

        label.appendChild(cb);
        label.appendChild(span);
        panel.appendChild(label);
    });
}

function applyGroupFilter() {
    let filtered = groupsFilterData.allLessons.filter(function (l) {
        return groupsFilterData.selectedIds.has(l.group.id);
    });
    updateAllLessonCells(filtered, 'class');

    // Toggling "relevant" on substitution rows avoids re-rendering the whole section
    updateSubstitutionHighlights();

    syncGroupFilterUrl();
}

function updateSubstitutionHighlights() {
    let rows = document.querySelectorAll('#substitutions-container tr[data-group-id]');
    rows.forEach(function (row) {
        let gid = parseInt(row.getAttribute('data-group-id'), 10);
        if (groupsFilterData.selectedIds.has(gid)) row.classList.add('relevant');
        else row.classList.remove('relevant');
    });
}

function syncGroupFilterUrl() {
    let allSelected = groupsFilterData.allGroups.every(function (g) {
        return groupsFilterData.selectedIds.has(g.id);
    });
    let url = new URL(window.location.href);

    if (allSelected || groupsFilterData.selectedIds.size === 0) {
        url.searchParams.delete('groups');
    } else {
        let sorted = Array.from(groupsFilterData.selectedIds).sort(function (a, b) {
            return a - b;
        });
        url.searchParams.set('groups', sorted.join(','));
    }
    // Keep commas readable in the address bar
    window.history.replaceState({}, '', url.toString().replace(/%2C/g, ','));
}

initGroupFilter();
