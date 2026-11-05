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

fs.mkdirSync(buildDir, { recursive: true });
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
