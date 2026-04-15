"use strict";

const { randomUUID } = require("crypto");
const pty = require("node-pty");

class SessionManager {
  constructor(opts = {}) {
    this.sessions = new Map();
    this.activeId = null;
    this.bufferSize = opts.bufferSize || 65536;
    this._stdin = null;
    this._resize = null;
    this._cleanup = () => this.detach();
    process.once("exit", this._cleanup);
    process.once("SIGINT", () => { this.detach(); process.exit(130); });
    process.once("SIGTERM", () => { this.detach(); process.exit(143); });
  }

  spawn(tool, args = [], cwd = process.cwd()) {
    const id = randomUUID();
    const proc = pty.spawn(tool, args, {
      cwd,
      env: process.env,
      name: "xterm-color",
      cols: process.stdout.columns || 80,
      rows: process.stdout.rows || 24,
    });
    const session = {
      id,
      tool,
      command: [tool].concat(args).join(" "),
      cwd,
      status: "running",
      createdAt: new Date().toISOString(),
      lastActivityAt: new Date().toISOString(),
      buffer: "",
      exitCode: null,
      signal: null,
      proc,
    };
    proc.onData((data) => {
      session.lastActivityAt = new Date().toISOString();
      session.buffer = (session.buffer + data).slice(-this.bufferSize);
      if (this.activeId === id) process.stdout.write(data);
    });
    proc.onExit(({ exitCode, signal }) => {
      session.status = "exited";
      session.exitCode = exitCode;
      session.signal = signal;
      if (this.activeId === id) this.detach();
    });
    this.sessions.set(id, session);
    return id;
  }

  attach(sessionId) {
    const session = this.sessions.get(sessionId);
    if (!session) throw new Error(`Unknown session: ${sessionId}`);
    if (session.status !== "running") throw new Error(`Session is ${session.status}: ${sessionId}`);
    if (this.activeId && this.activeId !== sessionId) this.detach();
    this.activeId = sessionId;
    if (session.buffer) process.stdout.write(session.buffer);
    this._stdin = (data) => session.proc.write(data);
    this._resize = () => session.proc.resize(process.stdout.columns || 80, process.stdout.rows || 24);
    if (process.stdin.isTTY) {
      process.stdin.setRawMode(true);
      process.stdin.resume();
    }
    process.stdin.on("data", this._stdin);
    process.stdout.on("resize", this._resize);
  }

  detach() {
    if (!this.activeId) return;
    if (this._stdin) process.stdin.off("data", this._stdin);
    if (this._resize) process.stdout.off("resize", this._resize);
    if (process.stdin.isTTY) process.stdin.setRawMode(false);
    this._stdin = null;
    this._resize = null;
    this.activeId = null;
  }

  list() {
    return Array.from(this.sessions.values())
      .filter((session) => session.status === "running")
      .map(({ proc, buffer, ...session }) => ({
        ...session,
        attached: session.id === this.activeId,
        bufferedBytes: Buffer.byteLength(buffer),
      }));
  }

  kill(sessionId) {
    const session = this.sessions.get(sessionId);
    if (!session) return false;
    if (this.activeId === sessionId) this.detach();
    session.proc.kill();
    this.sessions.delete(sessionId);
    return true;
  }
}

module.exports = SessionManager;
