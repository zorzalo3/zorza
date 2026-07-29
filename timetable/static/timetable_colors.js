"use strict";

function generateSubjectColor(subjectShort, seed = 2) {
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

function initializeSubjectColors(subjectList) {
    const seen = Object.create(null);
    let rules = '';

    subjectList.forEach(function(short) {
        if (short && !seen[short]) {
            seen[short] = true;
            rules += '.subject[data-subject="' + short.replace(/\\/g, '\\\\').replace(/"/g, '\\"') + '"]{color:' + generateSubjectColor(short) + '}';
        }
    });

    const el = document.createElement('style');
    el.textContent = rules;
    document.head.appendChild(el);
}