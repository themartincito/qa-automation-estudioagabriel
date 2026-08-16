module.exports = {
  ci: {
    collect: {
      url: [
        "https://www.estudioagabriel.com.ar",
        "https://estudioagabriel.ar",
      ],
      numberOfRuns: 1,
      settings: {
        preset: "desktop",
      },
    },
    upload: {
      target: "filesystem",
      outputDir: "./reports/lighthouse/desktop",
    },
  },
};
