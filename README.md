# Coins

Vyper implementation of the singleton multitoken design from [z0r0z/coins](https://github.com/z0r0z/coins).

The protocol extends the idea of **singletons**: token balances and permissions for many assets live in one contract instead of deploying a full ERC-20 for each new coin, which cuts state growth and deployment overhead. That direction matches z0r0z’s write-up on scaling via singletons, [How I would like to scale Ethereum with Singletons](https://z0r0z.eth.limo/).

## Original protocol

The Solidity reference implementation and specification live at [github.com/z0r0z/coins](https://github.com/z0r0z/coins). Credit for the original protocol goes to **z0r0z**, **0xc0de4c0ffee**, and **kobuta23**.

This repository is a Vyper port built with [Moccasin](https://cyfrin.github.io/moccasin). Behavior and the full feature set may differ from the upstream Solidity contracts—treat the GitHub repo as the canonical spec.

## What’s in this repo

| Path | Role |
|------|------|
| [`src/coins.vy`](src/coins.vy) | `Coins` registry: per-token metadata (`name`, `symbol`, `decimals` with max lengths **25** / **5**), aggregate supply, per-holder balances, allowances, ownership, and a mapping from numeric token id to façade (`_ids`). |
| [`src/tokens/erc20.vy`](src/tokens/erc20.vy) | Per-token façade (`erc20`): ERC-20-style surface (`transfer`, `transferFrom`, `approve`, `mint`, `burn`, `burnFrom`, `transferOwnership`, `renounceOwnership`) that forwards into `Coins` with immutable registry pointer (`COINS`) and façade id (`ID = convert(self, uint256)`). |

- **`Coins.create`** — `create_from_blueprint` deploys a façade bound to this registry, initializes metadata and sets the token owner to **`msg.sender`**, emits **`TokenCreated`** (`_id`, `_token`), returns the façade address.
- **Authorization** — Mutating registry functions include the token **`id`** as the first argument and require **`msg.sender == _ids[id]`** (the façade). Users and integrators normally call the façade; the registry is the shared backend.
- **Minting** — `mint` on the registry checks that the **`caller`** argument (the façade forwards `msg.sender`) is that token’s **`owner`** stored on `Coins`. There is no separate minter role in this port.

Compiler output and metadata are written under **`out/`** (see [`moccasin.toml`](moccasin.toml)).

## Lifecycle (this port)

On **`Coins`** (typically only the façade calls these):

- **`create`** — new façade + metadata + owner; emit `TokenCreated`; return façade address.

Via each coin’s façade (standard ERC-20 ergonomics; forwards into `Coins` with `ID`):

- **`mint`** — registry owner only (same note as above).
- **`transfer`**, **`transferFrom`**, **`approve`** — usual ERC-20 flow on the façade; registry updates balances and allowances under the façade id.
- **`burn`**, **`burnFrom`** — reduce supply; `burnFrom` consumes allowance where applicable.
- **`transferOwnership`**, **`renounceOwnership`** — owner updates on `Coins`; once there is no owner, **`mint`** reverts.

## Quickstart

1. Install dependencies (this repo uses **[uv](https://docs.astral.sh/uv/)**):

```bash
uv sync
```

2. Compile contracts:

```bash
mox compile
```

3. Run tests (`moccasin` discovers `tests/` and compiles from `src/`):

```bash
mox test
```

Local test setup deploys the façade as a **blueprint**, deploys **`Coins`** with that blueprint address, then uses **`Coins.create`** under pranks; see [`tests/conftest.py`](tests/conftest.py).

For CLI help: `mox --help` and the [Moccasin documentation](https://cyfrin.github.io/moccasin).

## Scripts

[`script/deploy.py`](script/deploy.py) deploys the erc20 blueprint and **`Coins`** registry (same ordering as tests), prints both addresses, and returns the registry wrapper when invoked via Moccasin:

```bash
mox run deploy
```

Use **`--network <name>`** (and wallet flags if needed) to target a live RPC—configured aliases live in [`moccasin.toml`](moccasin.toml) (`pyevm`, `anvil`, `sepolia`, `zksync-sepolia`, …).

## Deployments

Canonical **`Coins`** registry addresses and deployment blocks live in [`deployments.json`](deployments.json) (keyed by EIP-155 chain id).

| Chain | Chain id | `Coins` registry | Deployed at block |
|-------|----------|------------------|-------------------|
| Ethereum | `1` | [`0x0d3508A5bEB6DbF4C67282c38fb08674Ae2d1280`](https://etherscan.io/address/0x0d3508A5bEB6DbF4C67282c38fb08674Ae2d1280) | 25008464 |
| Base | `8453` | [`0xCebb1007277377f83F51651EBF94b18C0f99b62E`](https://basescan.org/address/0xCebb1007277377f83F51651EBF94b18C0f99b62E) | 45474723 |

Each coin’s façade is created with **`Coins.create`**; individual façade addresses are not listed in `deployments.json`.

## Linting

`mox lint` runs the **natrix** Vyper linter when installed (`uv tool install natrix`). Python formatting/lint for scripts and tests can use **ruff** from the project environment (for example `uv run ruff check .`).

## Safety

Contracts are marked **not production ready** and **not audited** in their NatSpec—treat them as experimental for learning and integration testing, not as a substitute for review before any onchain deployment.
