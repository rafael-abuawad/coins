# Coins

Vyper implementation of the singleton multitoken design from [z0r0z/coins](https://github.com/z0r0z/coins).

The protocol extends the idea of **singletons**: token balances and permissions for many assets live in one contract instead of deploying a full ERC-20 for each new coin, which cuts state growth and deployment overhead. That direction matches z0r0z’s write-up on scaling via singletons, [How I would like to scale Ethereum with Singletons](https://z0r0z.eth.limo/).

## Original protocol

The Solidity reference implementation and specification live at [github.com/z0r0z/coins](https://github.com/z0r0z/coins). Credit for the original protocol goes to **z0r0z**, **0xc0de4c0ffee**, and **kobuta23**.

This repository is a Vyper port built with [Moccasin](https://cyfrin.github.io/moccasin). Behavior and the full feature set may differ from the upstream Solidity contracts—treat the GitHub repo as the canonical spec.

## What’s in this repo

- A singleton [`Coins`](src/Coins.vy) registry: per-token metadata (name, symbol, decimals), aggregate supply, per-holder balances, allowances, ownership, plus a canonical mapping token id ↔ façade (`convert(facade, uint256)` is the id; the read-only accessor is `Coins.id`).
- Mutating hooks on `Coins` only succeed when `msg.sender` is that token’s registered façade (`_checkCallerIsToken`).
- Per-token façades spawned with [`create_from_blueprint`](src/Coins.vy); source is [`ERC20`](src/tokens/ERC20.vy). They expose ERC-20 transfers and approvals plus `mint`, `burn`, `burnFrom`, `transferOwnership`, and `renounceOwnership`, forwarding into `Coins` with an immutable façade id (`ID`).
- `create` registers a new coin: owner is `msg.sender`, façade address is recorded, logs `TokenCreated`.

## Lifecycle (this port)

On `Coins`:

- **`create`** — deploy a façade blueprint instance, initialize metadata and owner (`msg.sender`), emit `TokenCreated`, return façade address.

Via that coin’s façade (forwarded through `Coins`):

- **`mint`** — only the configured `owner` on `Coins` may mint (upstream may expose a distinct minter; this repo does **not**).
- **`transfer` / `transferFrom` / `approve`** — standard ERC-20 flow.
- **`burn`**, **`burnFrom`** — shrink supply (`burn` from caller balance; `burnFrom` burns from an owner’s balance when the caller is allowed).
- **`transferOwnership`**, **`renounceOwnership`** — façade-level admin mirrored on `Coins`; after renounce or moving owner to `empty(address)`, `mint` reverts.

## Quickstart

1. Install deps (repo uses **[uv](https://docs.astral.sh/uv/)**):

```bash
uv sync
```

2. Run tests (`moccasin` discovers `tests/` and compiles contracts from `src/`):

```bash
mox test
```

Deployment ordering in local tests mirrors what you’d do onchain: deploy the façade as a **blueprint**, deploy `Coins(blueprint)`, then callers invoke `Coins.create`; see [`tests/conftest.py`](tests/conftest.py).

For CLI help, run `mox --help` or see the [Moccasin documentation](https://cyfrin.github.io/moccasin).
