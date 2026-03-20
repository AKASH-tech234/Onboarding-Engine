const fs = require('fs');

// 1. index.css (containment classes)
let css = fs.readFileSync('../client/src/index.css', 'utf8');
if (!css.includes('.card-contain')) {
  css += `\n/* Performance Optimizations */\n.card-contain { contain: layout style paint; }\n.isolate-layer { isolation: isolate; }\n`;
  fs.writeFileSync('../client/src/index.css', css);
}

function patch(filePath, replacements) {
    let content = fs.readFileSync(filePath, 'utf8');
    replacements.forEach(([rgx, rep]) => {
        content = content.replace(rgx, rep);
    });
    fs.writeFileSync(filePath, content);
}

// 2. CourseNode.jsx (card contain, will-change, drop-shadow instead of shadow)
patch('../client/src/components/CourseNode.jsx', [
    [/className={`relative flex/g, 'className={`relative flex card-contain'],
    [/hover:-translate-y-1 /g, 'hover:-translate-y-1 will-change-transform '],
    [/shadow-\[/g, 'drop-shadow-[']
]);

// 3. TypewriterEffectSmooth.jsx (scale instead of width)
patch('../client/src/components/TypewriterEffectSmooth.jsx', [
    [/initial=\{\{ width: "0%" \}\}/g, 'initial={{ scaleX: 0 }}\n        style={{ transformOrigin: "left" }}'],
    [/whileInView=\{\{ width: "fit-content" \}\}/g, 'whileInView={{ scaleX: 1 }}']
]);

// 4. BackgroundGradient.jsx (transform translate instead of backgroundPosition, add will-change)
patch('../client/src/components/BackgroundGradient.jsx', [
    [/backgroundPosition: "0 50%"/g, 'x: "0%"'],
    [/backgroundPosition: \["0, 50%", "100% 50%", "0 50%"\]/g, 'x: ["-25%", "25%", "-25%"]'],
    [/style=\{\{ backgroundSize: animate \? "400% 400%" : undefined \}\}/g, 'style={{ backgroundSize: animate ? "400% 100%" : undefined, width: "200%", left: "-50%" }}']
]);

// 5. Strip backdrop-blur and add isolation
const noBlurFiles = [
    '../client/src/pages/UploadPage.jsx',
    '../client/src/components/UploadZone.jsx',
    '../client/src/components/PhaseTimeline.jsx',
    '../client/src/components/PathwayFlow.jsx',
    '../client/src/components/GapSummaryCard.jsx'
];

noBlurFiles.forEach(f => {
    patch(f, [
        [/ backdrop-blur-(sm|md|lg|xl|2xl|3xl|none)/g, ''],
        [/ backdrop-blur/g, ''],
        [/app-shell/g, 'app-shell isolate-layer'],
        [/flex h-full flex-col/g, 'flex h-full flex-col isolate-layer'],
        [/transition-all/g, 'transition-all will-change-transform'],
        [/transition-transform/g, 'transition-transform will-change-transform'],
        [/hover:shadow-\[/g, 'hover:drop-shadow-[']
    ]);
});

// 6. SkillChips.jsx
patch('../client/src/components/SkillChips.jsx', [
    [/hover:shadow-\[/g, 'hover:drop-shadow-['],
    [/transition-all/g, 'transition-all will-change-transform']
]);

console.log("Performance patches applied.");
