function cosineSimilarity(vectorA, vectorB) {
  if (!Array.isArray(vectorA) || !Array.isArray(vectorB)) {
    throw new Error("INVALID_VECTOR");
  }

  if (vectorA.length === 0 || vectorB.length === 0) {
    throw new Error("EMPTY_VECTOR");
  }

  if (vectorA.length !== vectorB.length) {
    throw new Error("VECTOR_LENGTH_MISMATCH");
  }

  let dotProduct = 0;
  let magnitudeA = 0;
  let magnitudeB = 0;

  for (let index = 0; index < vectorA.length; index += 1) {
    const valueA = Number(vectorA[index]);
    const valueB = Number(vectorB[index]);

    if (!Number.isFinite(valueA) || !Number.isFinite(valueB)) {
      throw new Error("INVALID_VECTOR_VALUE");
    }

    dotProduct += valueA * valueB;
    magnitudeA += valueA * valueA;
    magnitudeB += valueB * valueB;
  }

  if (magnitudeA === 0 || magnitudeB === 0) {
    return 0;
  }

  return dotProduct / (Math.sqrt(magnitudeA) * Math.sqrt(magnitudeB));
}

module.exports = {
  cosineSimilarity,
};
