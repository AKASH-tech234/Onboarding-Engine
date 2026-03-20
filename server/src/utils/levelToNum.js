const LEVEL_TO_NUM = {
  beginner: 1,
  intermediate: 2,
  advanced: 3,
};

const NUM_TO_LEVEL = {
  1: "beginner",
  2: "intermediate",
  3: "advanced",
};

function levelToNum(level) {
  if (typeof level !== "string") {
    throw new Error("INVALID_LEVEL");
  }

  const normalizedLevel = level.trim().toLowerCase();
  const value = LEVEL_TO_NUM[normalizedLevel];

  if (!value) {
    throw new Error(`UNKNOWN_LEVEL:${level}`);
  }

  return value;
}

function numToLevel(levelNum) {
  const value = NUM_TO_LEVEL[levelNum];

  if (!value) {
    throw new Error(`UNKNOWN_LEVEL_NUM:${levelNum}`);
  }

  return value;
}

module.exports = {
  LEVEL_TO_NUM,
  NUM_TO_LEVEL,
  levelToNum,
  numToLevel,
};
