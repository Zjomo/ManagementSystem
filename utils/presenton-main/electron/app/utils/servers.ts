import { ChildProcess, spawn } from "child_process";
import { localhost, logsDir } from "./constants";
import http from "http";
import fs from "fs";
import path from "path";

type ManagedChildProcess = ChildProcess & {
  pid?: number;
  killed?: boolean;
  exitCode?: number | null;
  signalCode?: NodeJS.Signals | null;
  __presentonExited?: boolean;
};

function makeChildEnv(env: FastApiEnv | NextJsEnv): NodeJS.ProcessEnv {
  return {
    ...process.env,
    PYTHONUTF8: process.env.PYTHONUTF8 ?? "1",
    PYTHONIOENCODING: process.env.PYTHONIOENCODING ?? "utf-8",
    PYTHONUNBUFFERED: process.env.PYTHONUNBUFFERED ?? "1",
    ...(env as Record<string, string | undefined>),
  };
}

function decodeLogChunk(data: Buffer | string): string {
  return Buffer.isBuffer(data) ? data.toString("utf8") : String(data);
}

function writeProcessLog(
  label: string,
  data: Buffer | string,
  stream: NodeJS.WriteStream,
) {
  const text = decodeLogChunk(data);
  const output = text
    .split(/\r?\n/)
    .filter((line) => line.length > 0)
    .map((line) => `${label}: ${line}`)
    .join("\n");
  if (output) {
    stream.write(`${output}\n`);
  }
}

export async function startFastApiServer(
  directory: string,
  port: number,
  env: FastApiEnv,
  isDev: boolean,
) {
  // Start FastAPI server
  let command: string;
  let args: string[];

  if (isDev) {
    command = "uv";
    args = ["run", "python", "server.py", "--port", port.toString(), "--reload", "true"];
  } else {
    const binary = process.platform === "win32" ? "fastapi.exe" : "fastapi";
    command = path.join(directory, binary);
    args = ["--port", port.toString()];
  }

  const safeLog = (data: Buffer | string, logPath: string) => {
    try {
      fs.appendFileSync(logPath, data);
    } catch {
      /* ignore if logs dir not writable */
    }
  };
  const fastapiLogPath = path.join(logsDir, "fastapi-server.log");

  const fastApiProcess = spawn(
    command,
    args,
    {
      cwd: directory,
      stdio: ["ignore", "pipe", "pipe"],
      env: makeChildEnv(env),
      windowsHide: process.platform === "win32" && !isDev,
    }
  );
  fastApiProcess.stdout.on("data", (data: any) => {
    safeLog(data, fastapiLogPath);
    writeProcessLog("FastAPI", data, process.stdout);
  });
  fastApiProcess.stderr.on("data", (data: any) => {
    safeLog(data, fastapiLogPath);
    writeProcessLog("FastAPI", data, process.stderr);
  });
  fastApiProcess.on("error", (err) => {
    safeLog(`Spawn error: ${err.message}\n`, fastapiLogPath);
  });
  fastApiProcess.once("exit", () => {
    (fastApiProcess as ManagedChildProcess).__presentonExited = true;
  });
  return {
    process: fastApiProcess,
    ready: waitForServer(`${localhost}:${port}/docs`, fastApiProcess, "FastAPI"),
  };
}

export async function startNextJsServer(
  directory: string,
  port: number,
  env: NextJsEnv,
  isDev: boolean,
) {
  let nextjsProcess: ManagedChildProcess;

  if (isDev) {
    // Windows: npm is npm.cmd; spawn() needs a shell or ENOENT.
    nextjsProcess = spawn(
      process.platform === "win32" ? "npm.cmd" : "npm",
      ["run", "dev", "--", "-p", port.toString(), "-H", "127.0.0.1"],
      {
        cwd: directory,
        stdio: ["ignore", "pipe", "pipe"],
        env: makeChildEnv(env),
        shell: process.platform === "win32",
      }
    );
    const nextjsLogPath = path.join(logsDir, "nextjs-server.log");
    const safeNextLog = (d: Buffer | string) => {
      try {
        fs.appendFileSync(nextjsLogPath, d);
      } catch {
        /* ignore */
      }
    };
    nextjsProcess.stdout!.on("data", (data: any) => {
      safeNextLog(data);
      writeProcessLog("NextJS", data, process.stdout);
    });
    nextjsProcess.stderr!.on("data", (data: any) => {
      safeNextLog(data);
      writeProcessLog("NextJS", data, process.stderr);
    });
    nextjsProcess.on("error", (err: Error) => {
      safeNextLog(`Spawn error: ${err.message}\n`);
      console.error(`NextJS spawn error: ${err.message}`);
    });
    nextjsProcess.on("exit", (code: number | null, signal: string | null) => {
      (nextjsProcess as ManagedChildProcess).__presentonExited = true;
      console.error(`NextJS process exited unexpectedly: code=${code}, signal=${signal}`);
    });
  } else {
    const serverScript = path.join(directory, "server.js");
    if (!fs.existsSync(serverScript)) {
      throw new Error(`Next.js standalone server not found: ${serverScript}`);
    }

    nextjsProcess = spawn(
      process.execPath,
      [serverScript],
      {
        cwd: directory,
        stdio: ["ignore", "pipe", "pipe"],
        env: {
          ...makeChildEnv(env),
          ...env,
          ELECTRON_RUN_AS_NODE: "1",
          HOSTNAME: "127.0.0.1",
          PORT: port.toString(),
        },
        windowsHide: process.platform === "win32",
      }
    );
    const nextjsLogPath = path.join(logsDir, "nextjs-server.log");
    const safeNextLog = (d: Buffer | string) => {
      try {
        fs.appendFileSync(nextjsLogPath, d);
      } catch {
        /* ignore */
      }
    };
    nextjsProcess.stdout!.on("data", (data: any) => {
      safeNextLog(data);
      writeProcessLog("NextJS", data, process.stdout);
    });
    nextjsProcess.stderr!.on("data", (data: any) => {
      safeNextLog(data);
      writeProcessLog("NextJS", data, process.stderr);
    });
    nextjsProcess.on("error", (err: Error) => {
      safeNextLog(`Spawn error: ${err.message}\n`);
      console.error(`NextJS spawn error: ${err.message}`);
    });
    nextjsProcess.on("exit", (code: number | null, signal: string | null) => {
      (nextjsProcess as ManagedChildProcess).__presentonExited = true;
      console.error(`NextJS process exited unexpectedly: code=${code}, signal=${signal}`);
    });
  }

  return {
    process: nextjsProcess,
    ready: waitForServer(`${localhost}:${port}`, nextjsProcess, "NextJS"),
  };
}


async function waitForServer(
  url: string,
  childProcess: ManagedChildProcess,
  label: string,
  timeout = 120000,
): Promise<void> {
  const startTime = Date.now();
  let exitError: Error | null = null;
  childProcess.once("exit", (code: number | null, signal: NodeJS.Signals | null) => {
    exitError = new Error(`${label} exited before it became ready: code=${code}, signal=${signal}`);
  });
  childProcess.once("error", (error: Error) => {
    exitError = new Error(`${label} failed to start: ${error.message}`);
  });

  while (Date.now() - startTime < timeout) {
    if (exitError) {
      throw exitError;
    }
    try {
      await new Promise<void>((resolve, reject) => {
        const req = http.get(url, (res) => {
          res.resume();
          if (res.statusCode && res.statusCode >= 200 && res.statusCode < 500) {
            resolve();
          } else {
            reject(new Error(`Unexpected status code: ${res.statusCode}`));
          }
        });
        req.on('error', reject);
        req.setTimeout(5000, () => {
          req.destroy();
          reject(new Error('Request timed out'));
        });
      });
      return;
    } catch (error) {
      if (exitError) {
        throw exitError;
      }
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
  throw new Error(`${label} did not start at ${url} within ${timeout}ms`);
}
