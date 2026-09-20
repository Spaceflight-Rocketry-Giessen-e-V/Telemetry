const customCppTypes = new Set([
  "buttonStruct",
  "char_Component",
  "cobs_Component",
  "Component",
  "const_Component",
  "dataStruct",
  "empty_Component",
  "float_Component",
  "ledStruct",
  "Packet",
  "parity_Component",
  "RC17xxHP_RC232",
  "Subsystem",
  "uint8_t_Component",
  " HardwareSerial",
]);

document$.subscribe(() => {
  const identifiers = document.querySelectorAll(
    '.language-cpp .n, [class~="language-C++"] .n'
  );

  identifiers.forEach((identifier) => {
    if (customCppTypes.has(identifier.textContent.trim())) {
      identifier.classList.replace("n", "kt");
    }
  });
});
