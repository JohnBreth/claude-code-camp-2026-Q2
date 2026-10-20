#!/usr/bin/env python3
"""Persistent tbaMUD session: a background daemon holds the TCP connection; CLI calls talk to it over a Unix socket."""
import json, os, re, socket, subprocess, sys, threading, time

HOST = os.environ.get("MUD_HOST", "localhost")
PORT = int(os.environ.get("MUD_PORT", "4000"))
USER = os.environ.get("MUD_USER", "dummy")
PASS = os.environ.get("MUD_PASS", "helloworld")
DIR = f"/tmp/play-mud-{os.getuid()}"
SOCK, LOG = f"{DIR}/ctl.sock", f"{DIR}/session.log"
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def strip_telnet(data, state):
    out = bytearray()
    for b in data:
        if state[0] == "data":
            if b == 255: state[0] = "iac"
            else: out.append(b)
        elif state[0] == "iac":
            state[0] = {250: "sb", 255: "data"}.get(b, "opt" if 251 <= b <= 254 else "data")
            if b == 255: out.append(255)
        elif state[0] == "opt":
            state[0] = "data"
        elif state[0] == "sb":
            if b == 255: state[0] = "sb_iac"
        elif state[0] == "sb_iac":
            state[0] = "data" if b == 240 else "sb"
    return bytes(out)


class Session:
    def __init__(self):
        self.buf, self.read_pos, self.last_rx = "", 0, time.time()
        self.cv = threading.Condition()
        self.alive = True
        self.mud = socket.create_connection((HOST, PORT), timeout=10)
        self.mud.settimeout(None)
        self.log = open(LOG, "a")
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self):
        state = ["data"]
        while True:
            try:
                data = self.mud.recv(4096)
            except OSError:
                data = b""
            with self.cv:
                if not data:
                    self.alive = False
                    self.cv.notify_all()
                    return
                text = ANSI.sub("", strip_telnet(data, state).decode("latin-1")).replace("\r", "")
                self.buf += text
                self.last_rx = time.time()
                self.log.write(text); self.log.flush()
                self.cv.notify_all()

    def write(self, line):
        self.mud.sendall(line.encode("latin-1") + b"\r\n")

    def wait_for(self, patterns, timeout, start):
        deadline = time.time() + timeout
        with self.cv:
            while self.alive and time.time() < deadline:
                for p in patterns:
                    if p in self.buf[start:]:
                        return p
                self.cv.wait(deadline - time.time())
        return None

    def settle(self, quiet=0.5, timeout=5.0, start=None):
        deadline = time.time() + timeout
        with self.cv:
            while self.alive and time.time() < deadline:
                gap = time.time() - self.last_rx
                if gap >= quiet and (start is None or len(self.buf) > start):
                    return
                if gap >= quiet:
                    self.cv.wait(deadline - time.time())
                    continue
                self.cv.wait(min(quiet - gap, deadline - time.time()))

    def unread(self):
        with self.cv:
            out, self.read_pos = self.buf[self.read_pos:], len(self.buf)
        return out

    def login(self):
        pos, sent_name = 0, False
        steps = {"By what name": USER, "Password:": PASS, "Wrong password": None,
                 "PRESS RETURN": "", "Make your choice": "1"}
        while True:
            hit = self.wait_for(list(steps), 8, pos)
            if hit is None:
                break
            pos = self.buf.index(hit, pos) + len(hit)
            if hit == "Wrong password" or (hit == "By what name" and sent_name):
                raise RuntimeError("login rejected (bad name/password?)")
            sent_name |= hit == "By what name"
            self.write(steps[hit])
            if hit == "Make your choice":
                break
        self.settle()

    def logout(self):
        if self.alive:
            pos = len(self.buf)
            self.write("quit")
            if self.wait_for(["Make your choice"], 3, pos):
                self.write("0")
        self.mud.close()


def serve():
    os.makedirs(DIR, exist_ok=True)
    try:
        s = Session()
        s.login()
    except Exception as e:
        open(f"{DIR}/error", "w").write(str(e))
        return
    if os.path.exists(SOCK):
        os.unlink(SOCK)
    ctl = socket.socket(socket.AF_UNIX)
    ctl.bind(SOCK); ctl.listen(4); ctl.settimeout(1)
    try:
        while s.alive:
            try:
                conn, _ = ctl.accept()
            except socket.timeout:
                continue
            with conn:
                req = json.loads(conn.makefile().readline())
                if req["op"] == "send":
                    start = len(s.buf)
                    s.write(req["cmd"])
                    s.settle(req.get("quiet", 0.5), req.get("timeout", 5), start)
                elif req["op"] == "wait":
                    s.settle(req.get("quiet", 1.0), req.get("timeout", 10))
                elif req["op"] == "stop":
                    s.logout()
                conn.sendall(s.unread().encode("latin-1", "replace"))
                if req["op"] == "stop":
                    break
            if not s.alive:
                break
    finally:
        ctl.close()
        os.path.exists(SOCK) and os.unlink(SOCK)


def call(req):
    c = socket.socket(socket.AF_UNIX)
    try:
        c.connect(SOCK)
    except OSError:
        sys.exit("not connected - run: mud.py start")
    c.sendall(json.dumps(req).encode() + b"\n")
    chunks = []
    while chunk := c.recv(65536):
        chunks.append(chunk)
    return b"".join(chunks).decode("latin-1")


def main():
    args = sys.argv[1:]
    op = args[0] if args else "help"
    if op == "_serve":
        serve()
    elif op == "start":
        if os.path.exists(SOCK):
            print(call({"op": "wait", "quiet": 0.2, "timeout": 1}) or "(already connected)")
            return
        os.makedirs(DIR, exist_ok=True)
        err = f"{DIR}/error"
        os.path.exists(err) and os.unlink(err)
        subprocess.Popen([sys.executable, __file__, "_serve"], start_new_session=True,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=open(f"{DIR}/daemon.err", "a"))
        for _ in range(150):
            if os.path.exists(SOCK) or os.path.exists(err):
                break
            time.sleep(0.1)
        if os.path.exists(err):
            sys.exit("login failed: " + open(err).read())
        print(call({"op": "wait", "quiet": 0.2, "timeout": 1}))
    elif op == "send" and len(args) >= 2:
        print(call({"op": "send", "cmd": " ".join(args[1:])}))
    elif op == "wait":
        print(call({"op": "wait", "timeout": float(args[1]) if len(args) > 1 else 10}))
    elif op == "stop":
        print(call({"op": "stop"}))
    elif op == "status":
        print("connected" if os.path.exists(SOCK) else "not connected")
    else:
        print("usage: mud.py start | send <command...> | wait [secs] | status | stop")


if __name__ == "__main__":
    main()
