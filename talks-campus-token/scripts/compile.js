// Compiles every contract in contracts/ into build/<Name>.json (abi + bytecode).
// Usage: node scripts/compile.js
const fs = require("fs");
const path = require("path");
const solc = require("solc");

const root = path.join(__dirname, "..");
const contractsDir = path.join(root, "contracts");
const buildDir = path.join(root, "build");

const sources = {};
for (const file of fs.readdirSync(contractsDir).filter((f) => f.endsWith(".sol"))) {
  sources[`contracts/${file}`] = { content: fs.readFileSync(path.join(contractsDir, file), "utf8") };
}

const input = {
  language: "Solidity",
  sources,
  settings: {
    optimizer: { enabled: true, runs: 200 },
    evmVersion: "paris",
    outputSelection: { "*": { "*": ["abi", "evm.bytecode.object"] } },
  },
};

function findImports(importPath) {
  const candidates = [path.join(root, "node_modules", importPath), path.join(root, importPath)];
  for (const p of candidates) {
    if (fs.existsSync(p)) return { contents: fs.readFileSync(p, "utf8") };
  }
  return { error: `Not found: ${importPath}` };
}

const output = JSON.parse(solc.compile(JSON.stringify(input), { import: findImports }));
const errors = (output.errors || []).filter((e) => e.severity === "error");
for (const e of output.errors || []) console.error(e.formattedMessage);
if (errors.length) process.exit(1);

// Adapted from the teammate's verification export. Include every imported source.
const fullSources = { ...sources };
for (const file of Object.keys(output.sources)) {
  if (!fullSources[file]) {
    const imported = findImports(file);
    if (!imported.contents) throw new Error("Cannot export " + file);
    fullSources[file] = { content: imported.contents };
  }
}
const standardInput = { ...input, sources: fullSources };
const reproduced = JSON.parse(solc.compile(JSON.stringify(standardInput)));
if ((reproduced.errors || []).some(e => e.severity === "error")) {
  throw new Error("Self-contained Standard JSON failed: " + JSON.stringify(reproduced.errors));
}
for (const [file, contracts] of Object.entries(output.contracts)) {
  if (!file.startsWith("contracts/")) continue;
  for (const [name, c] of Object.entries(contracts)) {
    if (c.evm.bytecode.object !== reproduced.contracts[file][name].evm.bytecode.object)
      throw new Error("Verification input does not reproduce bytecode: " + name);
  }
}
fs.mkdirSync(buildDir, { recursive: true });
fs.writeFileSync(path.join(buildDir, "standard-input.json"), JSON.stringify(standardInput, null, 2));
fs.writeFileSync(path.join(buildDir, "compiler.txt"), "v" + solc.version().replace(".Emscripten.clang", "") + "\n");
for (const [file, contracts] of Object.entries(output.contracts)) {
  if (!file.startsWith("contracts/")) continue;
  for (const [name, c] of Object.entries(contracts)) {
    fs.writeFileSync(
      path.join(buildDir, `${name}.json`),
      JSON.stringify({ abi: c.abi, bytecode: "0x" + c.evm.bytecode.object }, null, 2)
    );
    console.log(`compiled ${name}`);
  }
}
