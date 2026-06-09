const { spawn, spawnSync } = require("child_process");

const electron = require("electron");

if (process.platform === "win32") {
  try {
    spawnSync("cmd.exe", ["/d", "/c", "chcp 65001>nul"], { stdio: "ignore" });
  } catch {
    // Keep startup best-effort; encoding is also handled in child env.
  }
}

const env = {
  ...process.env,
  LANG: process.env.LANG || "C.UTF-8",
  LC_ALL: process.env.LC_ALL || "C.UTF-8",
  PYTHONUTF8: process.env.PYTHONUTF8 || "1",
  PYTHONIOENCODING: process.env.PYTHONIOENCODING || "utf-8",
  PYTHONUNBUFFERED: process.env.PYTHONUNBUFFERED || "1",
};
delete env.ELECTRON_RUN_AS_NODE;

const child = spawn(electron, [".", "--no-sandbox", ...process.argv.slice(2)], {
  cwd: __dirname,
  env,
  stdio: "inherit",
  windowsHide: false,
});

child.on("close", (code, signal) => {
  if (signal) {
    console.error(`${electron} exited with signal ${signal}`);
    process.exit(1);
  }
  process.exit(code ?? 0);
});

for (const signal of ["SIGINT", "SIGTERM"]) {
  process.on(signal, () => {
    if (!child.killed) {
      child.kill(signal);
    }
  });
}
