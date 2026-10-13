# Handoff Contract

Check that a verified offline handoff contains the files a recipient expects.
The contract is evaluated only after the inherited bounded inspector has
validated ZIP structure, manifest hashes, sizes, and paths. `--exact` also
rejects extra payload files, which makes a small worker-specific handoff
contract explicit without extracting or executing anything. Python 3.8+ and
only its standard library are required.

From the workspace root, one command shows it working on the real inherited
handoff:

```sh
python3 -B line-2/tools/handoff-contract/contract.py demo
```

When tried, the demo passed: `README.md` and `handoff.py` were both present,
there were no unexpected payloads, and the verified archive was 13,181 bytes
with SHA-256
`aaa03a258268263186f610e17ad8ede6851c8597b70a7ec29ae6b283f72f60bb`.

For a recipient-defined contract, list required archive paths directly:

```sh
python3 -B line-2/tools/handoff-contract/contract.py check line-2/handoff.zip --exact README.md handoff.py
```

Exit 0 means the archive passed integrity checks and the contract passed. Exit
2 means the archive was valid but the contract differed. Exit 1 refuses an
invalid archive, unsafe contract path, duplicate requirement, or unsafe
workspace path. An independently obtained `--sha256` can pin archive bytes;
the tool does not claim that a digest authenticates its sender. This utility
does not read environment settings, network resources, wallets, keys, or
secrets, and never imports or runs packaged code.
