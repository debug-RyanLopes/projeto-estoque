/** Fonte da verdade das cores/tema. O CSS final é gerado por `make css`. */
module.exports = {
  content: ["./app/templates/**/*.html"],
  theme: {
    extend: {
      colors: {
        moss: {
          DEFAULT: "#009394",
          dark: "#006270",
          light: "#00E0C7",
          bg: "#2B3548",
          contrast: "#424769",
        },
      },
    },
  },
};
