module.exports = {
  ci: {
    collect: {
      url: [
        "https://www.estudioagabriel.com.ar",
        "https://estudioagabriel.ar",
      ],
      numberOfRuns: 1,
      // Sin "preset: desktop" -> Lighthouse usa su perfil mobile por defecto,
      // con throttling simulado equivalente a una conexión 4G media (~1.6 Mbps).
    },
    upload: {
      target: "filesystem",
      outputDir: "./reports/lighthouse/mobile",
    },
  },
};
