"use strict";

const DOM = {
    classSelect: document.getElementById('timetable-select-class'),
    teacherSelect: document.getElementById('timetable-select-teacher'),
    roomSelect: document.getElementById('timetable-select-room'),
}

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
let lastUpdate = timetable_init_data?.last_update || 0; // Timetable last update (UNIX timestamp)

function setCurrentPath() {
    currentPath = window.location.pathname + window.location.search;
}

function initDefaultButton() {
    setCurrentPath();
    if (defaultButton) {
        // Search exact match
        const isExactlyDefault = document.cookie.split(';').some(item => {
            const trimmed = item.trim();
            const eqIndex = trimmed.indexOf('=');
            if (eqIndex === -1) return false;
            const key = trimmed.substring(0, eqIndex);
            const value = trimmed.substring(eqIndex + 1);
            return key === defaultCookieKey && value === currentPath;
        });

        if (!isExactlyDefault) {
            defaultButton.style.visibility = "visible";
        } else {
            defaultButton.style.visibility = "hidden";
        }
    }
}

initDefaultButton();

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
    let timerElement, until;
    // timer - the <span> element which should be shown
    // until - time to which it is count down

    if (now < periods[0].beginTime) {
        // If it's before all lessons

        if (addMinutes(now, 60) < periods[0].beginTime) {
            return;
        }

        timerElement = document.getElementById("before-lessons");
        until = periods[0].beginTime;
    } else if (now > periods[periods.length - 1].endTime) {
        // If it's after all lessons
        timerElement = document.getElementById("after-lessons");
    } else for (var i = 0; i < periods.length; i++) {
        if (periods[i].beginTime < now && now < periods[i].endTime) {
            // If a lesson is ongoing
            timerElement = document.getElementById("during-lesson");
            let tmp = document.getElementById("period-" + periods[i]['number']);
            if (tmp) {
                let row = tmp.parentElement;
                row.classList.add("highlight");
                prevHighlight = row;
            }
            until = periods[i].endTime;
            let period_no = timerElement.getElementsByClassName("period-no")[0];
            period_no.textContent = periods[i].number;
            break;
        }
        if (i > 0 && periods[i - 1].endTime < now && now < periods[i].beginTime) {
            // If it's a break between lessons
            timerElement = document.getElementById("between-lessons");
            let tmp = document.getElementById("period-" + periods[i - 1]['number']);
            if (tmp) {
                let row = tmp.parentElement;
                row.classList.add("break-highlight");
                prevHighlight = row;
            }
            until = periods[i].beginTime;
            let period_no = timerElement.getElementsByClassName("period-no")[0];
            period_no.textContent = periods[i].number;
            break;
        }
    }
    if (prevTimer) prevTimer.setAttribute("hidden", "true");
    prevTimer = timerElement;
    if (timerElement) {
        timerElement.removeAttribute("hidden");
        if (until) {
            timerElement.getElementsByTagName("time")[0].textContent = toDisplay(until - now);
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
        '<span class="subject" data-subject="' + esc(s.short_name) + '" title="' + esc(s.name) + '">' + esc(s.short_name) + '</span>' +
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
    if (!timetable_init_data || timetable_init_data.type !== 'class') return;

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

    // Only show the groups section when there are multiple groups to choose from
    let groupsSection = document.getElementById('groups-section');
    if (groupsSection && data.groups.length > 1) {
        groupsSection.style.display = '';
        renderGroupCheckboxes();
    }
}

function renderGroupCheckboxes() {
    let panel = document.getElementById('group-filter-panel');
    if (!panel) return;

    let groups = groupsFilterData.allGroups.slice();

    groups.forEach(function (group) {
        let label = document.createElement('label');
        label.className = 'persona-group-label';

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

    renderSchedule();
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
    initDefaultButton();
}

initGroupFilter();

let colorsEnabled = localStorage.getItem('subjectColorsEnabled') === 'true';

function setColorsEnabled(val) {
    colorsEnabled = val;
    localStorage.setItem('subjectColorsEnabled', String(val));
}

function subjectColorRaw(subjectShort, seed = 2) {
    const custom = localStorage.getItem('subjectColor_' + subjectShort);
    if (custom) return custom;

    let h = seed;
    const s = subjectShort || '';

    for (let i = 0; i < s.length; i++) {
        h = (Math.imul(31, h) + s.charCodeAt(i)) | 0;
    }

    const goldenRatioConjugate = 0.618033988749895;
    let hueFraction = (Math.abs(h) * goldenRatioConjugate) % 1;

    const minHue = 70;
    const maxHue = 320;
    const hue = Math.floor(minHue + hueFraction * (maxHue - minHue));

    const saturationOptions = [50, 65, 80];
    const saturation = saturationOptions[Math.abs(h >> 4) % saturationOptions.length];

    const lightnessOptions = [45, 55, 65];
    const lightness = lightnessOptions[Math.abs(h >> 8) % lightnessOptions.length];

    return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

function subjectColor(subjectShort, seed = 2) {
    if (!colorsEnabled) return 'inherit';
    return subjectColorRaw(subjectShort, seed);
}

// Converts hsl(...) string or hex string to a #rrggbb hex value for <input type="color">.
function colorToHex(color) {
    if (!color) return '#4da8dc';
    if (color.startsWith('#')) return color;
    const match = color.match(/hsl\(\s*(\d+)\s*,\s*(\d+)%\s*,\s*(\d+)%\s*\)/);
    if (!match) return '#4da8dc';
    let h = parseInt(match[1]) / 360;
    const s = parseInt(match[2]) / 100;
    const l = parseInt(match[3]) / 100;
    let r, g, b;
    if (s === 0) {
        r = g = b = l;
    } else {
        const hue2rgb = (p, q, t) => {
            if (t < 0) t += 1;
            if (t > 1) t -= 1;
            if (t < 1 / 6) return p + (q - p) * 6 * t;
            if (t < 1 / 2) return q;
            if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
            return p;
        };
        const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
        const p = 2 * l - q;
        r = hue2rgb(p, q, h + 1 / 3);
        g = hue2rgb(p, q, h);
        b = hue2rgb(p, q, h - 1 / 3);
    }
    const toHex = x => Math.round(x * 255).toString(16).padStart(2, '0');
    return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

function renderSchedule() {
    if (groupsFilterData.allLessons) {
        applyGroupFilter();
        return;
    }
    // teacher / room timetable: update a dynamic <style> block in place
    let dynamicStyle = document.getElementById('dynamic-subject-colors');
    if (!dynamicStyle) {
        dynamicStyle = document.createElement('style');
        dynamicStyle.id = 'dynamic-subject-colors';
        document.head.appendChild(dynamicStyle);
    }
    if (!colorsEnabled) {
        dynamicStyle.textContent = '';
        return;
    }
    const seen = Object.create(null);
    let rules = '';
    document.querySelectorAll('.subject[data-subject]').forEach(function (el) {
        const short = el.getAttribute('data-subject');
        if (short && !seen[short]) {
            seen[short] = true;
            rules += '.subject[data-subject="' + short.replace(/\\/g, '\\\\').replace(/"/g, '\\"') + '"]{color:' + subjectColorRaw(short) + '}';
        }
    });
    dynamicStyle.textContent = rules;
}

function initPersonalizationAccordion() {
    const sections = [
        { toggleId: 'colors-section-toggle', contentId: 'colors-section-content', arrowId: 'colors-section-arrow' },
        { toggleId: 'groups-section-toggle', contentId: 'groups-section-content', arrowId: 'groups-section-arrow' },
    ];

    sections.forEach(function (sec) {
        let content = document.getElementById(sec.contentId);
        if (content) content.classList.add('persona-section-content--closed');
    });

    sections.forEach(function (sec) {
        let toggle = document.getElementById(sec.toggleId);
        let content = document.getElementById(sec.contentId);
        let arrow = document.getElementById(sec.arrowId);
        if (!toggle || !content) return;

        toggle.addEventListener('click', function () {
            let isNowOpen = content.classList.contains('persona-section-content--closed');

            // Close all sections first
            sections.forEach(function (other) {
                let otherContent = document.getElementById(other.contentId);
                let otherArrow = document.getElementById(other.arrowId);
                if (otherContent) otherContent.classList.add('persona-section-content--closed');
                if (otherArrow) otherArrow.innerHTML = '&#9660;'; // ▼
            });

            // Open clicked section if it was closed
            if (isNowOpen) {
                content.classList.remove('persona-section-content--closed');
                if (arrow) arrow.innerHTML = '&#9650;'; // ▲
            }
        });
    });
}

function initColorModal() {
    const btn = document.getElementById('personalization-btn');
    const modal = document.getElementById('personalization-modal');
    const closeBtn = document.getElementById('personalization-modal-close');
    const toggleInput = document.getElementById('color-toggle-input');
    const subjectsList = document.getElementById('color-subjects-list');
    const iroContainer = document.getElementById('color-iro-container');
    const iroSubjectName = document.getElementById('color-iro-subject-name');
    if (!btn || !modal) return;

    let iroPicker = null;
    let selectedSwatch = null;
    let selectedShort = null;
    let isSilent = false;

    function initIroPicker() {
        if (iroPicker || !window.iro) return;
        iroPicker = new window.iro.ColorPicker('#color-iro-picker', {
            width: 200,
            color: '#4da8dc',
            layout: [
                { component: window.iro.ui.Wheel },
                { component: window.iro.ui.Slider, options: { sliderType: 'value' } },
            ],
            borderWidth: 1,
            borderColor: '#2a313e',
            handleRadius: 8,
        });

        iroPicker.on('color:change', color => {
            if (isSilent || !selectedShort) return;
            const hex = color.hexString;
            if (selectedSwatch) selectedSwatch.style.background = hex;
            localStorage.setItem('subjectColor_' + selectedShort, hex);
            renderSchedule();
        });
    }

    function selectSwatch(swatchEl, short, name) {
        if (selectedSwatch) selectedSwatch.classList.remove('selected');
        selectedSwatch = swatchEl;
        selectedShort = short;
        swatchEl.classList.add('selected');

        if (iroSubjectName) iroSubjectName.textContent = name;
        if (iroContainer) iroContainer.style.display = 'flex';

        initIroPicker();
        if (iroPicker) {
            isSilent = true;
            iroPicker.color.hexString = colorToHex(subjectColorRaw(short));
            isSilent = false;
        }
    }

    function updateToggle() {
        if (toggleInput) toggleInput.checked = colorsEnabled;
    }

    function populateSubjects() {
        const seen = {};
        if (groupsFilterData.allLessons) {
            groupsFilterData.allLessons.forEach(lesson => {
                const short = lesson.subject.short_name;
                if (short && !seen[short]) seen[short] = lesson.subject.name || short;
            });
        } else {
            document.querySelectorAll('.subject[data-subject]').forEach(function (el) {
                const short = el.getAttribute('data-subject');
                const name = el.getAttribute('title') || short;
                if (short && !seen[short]) seen[short] = name;
            });
        }

        subjectsList.innerHTML = '';
        selectedSwatch = null;
        selectedShort = null;
        if (iroContainer) iroContainer.style.display = 'none';

        Object.entries(seen)
            .sort((a, b) => a[1].localeCompare(b[1], 'pl'))
            .forEach(([short, name]) => {
                const row = document.createElement('div');
                row.className = 'color-subject-row';

                const label = document.createElement('span');
                label.className = 'color-subject-name';
                label.textContent = name;

                const swatch = document.createElement('button');
                swatch.className = 'color-swatch-btn';
                swatch.style.background = colorToHex(subjectColorRaw(short));
                swatch.title = (typeof TIMETABLE_I18N !== 'undefined') ? TIMETABLE_I18N.clickToChangeColor : 'Kliknij, aby zmienić kolor';
                swatch.type = 'button';
                swatch.addEventListener('click', () => selectSwatch(swatch, short, name));

                row.appendChild(label);
                row.appendChild(swatch);
                subjectsList.appendChild(row);
            });
    }

    function openModal() {
        populateSubjects();
        updateToggle();
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    function closeModal() {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }

    btn.addEventListener('click', openModal);
    closeBtn.addEventListener('click', closeModal);
    modal.addEventListener('click', e => { if (e.target === modal) closeModal(); });
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal.style.display === 'flex') closeModal();
    });
    toggleInput.addEventListener('change', () => {
        setColorsEnabled(toggleInput.checked);
        renderSchedule();
    });
}

async function getLastUpdate() {
    try {
        const response = await fetch('/timetable/api/1/last_update/');
        
        const data = await response.json();
        
        return data.last_update;
    } catch (error) {
        return null;
    }
}

function init() {
    initColorModal();
    initPersonalizationAccordion();
    
    window.addEventListener('visibilitychange', async (e) => {
        if (document.visibilityState !== 'visible') return;
        
        try {
            const serverLastUpdate = await getLastUpdate();
            
            // console.log("Server last update:", serverLastUpdate, "Current last update:", lastUpdate);
            
            if (serverLastUpdate && serverLastUpdate > lastUpdate) {
                // If the timetable was updated while the user had the page open in another tab, reload to get fresh data.
                window.location.reload();
                lastUpdate = serverLastUpdate;
            }
        } catch (error) {
            console.error("Error checking for timetable updates:", error);
        }
    });
}

document.addEventListener('DOMContentLoaded', init);