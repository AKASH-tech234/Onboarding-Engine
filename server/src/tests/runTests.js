const { runComputeSkillGapTests } = require("./computeSkillGap.test");
const { runAdaptivePathwayTests } = require("./adaptivePathway.test");
const { runLoggerTests } = require("./logger.test");

async function main() {
  const suites = [
    { name: "computeSkillGap", run: runComputeSkillGapTests },
    { name: "adaptivePathway", run: runAdaptivePathwayTests },
    { name: "logger", run: runLoggerTests },
  ];

  for (const suite of suites) {
    await suite.run();
    process.stdout.write("[PASS] " + suite.name + "\n");
  }

  process.stdout.write("[PASS] all tests\n");
}

main().catch((error) => {
  process.stderr.write("[FAIL] " + (error && error.stack ? error.stack : String(error)) + "\n");
  process.exit(1);
});
