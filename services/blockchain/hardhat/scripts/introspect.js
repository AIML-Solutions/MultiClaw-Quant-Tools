const hre = require("hardhat");

async function main() {
  const contractName = process.argv[2] || "Greeter";
  await hre.run("compile");

  const artifact = await hre.artifacts.readArtifact(contractName);

  const fns = artifact.abi.filter((x) => x.type === "function").map((f) => ({
    name: f.name,
    stateMutability: f.stateMutability,
    inputs: (f.inputs || []).map((i) => `${i.type} ${i.name}`),
    outputs: (f.outputs || []).map((o) => `${o.type} ${o.name}`),
  }));

  const report = {
    contract: contractName,
    bytecodeLength: artifact.bytecode ? artifact.bytecode.length : 0,
    deployedBytecodeLength: artifact.deployedBytecode ? artifact.deployedBytecode.length : 0,
    functions: fns,
  };

  console.log(JSON.stringify(report, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
