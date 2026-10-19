"""WP2: re-check the optional round 12 sources on origin; copy what is there and append (or replace) an
'Added at WP2' section in sources/SOURCES.md. The WP0 record above it is kept."""
import datetime, hashlib, json, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__)); ST = os.path.dirname(HERE)
MAIN = "/Users/shane/Desktop/Arena_1013_model"
REF = "origin/exp/phase2-r12-eps-level-20261019"
ROOT = "research/phase2_r12_eps_level_20261019"
FILES = [("wp3/pairs.csv", "r12/wp3_pairs.csv", "prompt WP2 N cross-check"),
         ("src/ahchain.py", "r12/ahchain.py", "descriptive N cross-check only (registered chain unchanged, D4/D10)")]
MARK = "## Added at WP2"


def git(*a):
    return subprocess.run(["git", "-C", MAIN] + list(a), capture_output=True)


def main():
    git("fetch", "origin")
    commit = git("rev-parse", "--short", REF).stdout.decode().strip()
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines, status = [MARK, "", f"Re-checked {stamp} after `git fetch origin`; `{REF}` at `{commit}`.", "",
                     "| copy | path at ref | use | SHA256 / status |", "|---|---|---|---|"], {}
    for rel, dst, use in FILES:
        r = git("show", f"{REF}:{ROOT}/{rel}")
        if r.returncode != 0:
            lines.append(f"| — | `{ROOT}/{rel}` | {use} | not available |")
            status[rel] = "not available"
            continue
        out = os.path.join(ST, "sources", dst)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "wb").write(r.stdout)
        h = hashlib.sha256(r.stdout).hexdigest()
        lines.append(f"| `{dst}` | `{ROOT}/{rel}` | {use} | `{h}` |")
        status[rel] = {"copy": dst, "sha256": h, "commit": commit}
    path = os.path.join(ST, "sources", "SOURCES.md")
    text = open(path).read()
    head, _, rest = text.partition(MARK)
    later = rest[rest.find("\n## "):] if "\n## " in rest else ""   # keep sections added after WP2 (WP3)
    open(path, "w").write(head.rstrip("\n") + "\n\n" + "\n".join(lines) + "\n" + later)
    json.dump({"checked": stamp, "commit": commit, "files": status},
              open(os.path.join(ST, "cache", "wp2_sources.json"), "w"), indent=1)
    print(json.dumps(status, indent=1))


if __name__ == "__main__":
    main()
