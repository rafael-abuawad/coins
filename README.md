# Coins

Vyper implementation of the singleton multitoken design from [z0r0z/coins](https://github.com/z0r0z/coins).

The protocol extends the idea of **singletons**: token balances and permissions for many assets live in one contract instead of deploying a full ERC-20 for each new coin, which cuts state growth and deployment overhead. That direction matches z0r0z’s write-up on scaling via singletons, [How I would like to scale Ethereum with Singletons](https://z0r0z.eth.limo/).

## Original protocol

The Solidity reference implementation and specification live at [github.com/z0r0z/coins](https://github.com/z0r0z/coins). Credit for the original protocol goes to **z0r0z**, **0xc0de4c0ffee**, and **kobuta23**.

This repository is a Vyper port built with [Moccasin](https://cyfrin.github.io/moccasin). Behavior and the full feature set may differ from the upstream Solidity contracts—treat the GitHub repo as the canonical spec.

## What’s in this repo

- A singleton [`Coins`](src/Coins.vy) contract holding names, symbols, decimals, supplies, balances, allowances, owners, and minters keyed by token id (the id matches the per-coin ERC-20 contract address).
- Per-coin ERC-20 facades deployed with `create_from_blueprint` ([`ERC20`](src/tokens/ERC20.vy)); they expose standard ERC-20-style entrypoints and forward state changes to `Coins`.
- `Coins` only accepts balance and allowance updates when `msg.sender` is the token for that id, so users and integrations interact through the lightweight ERC-20 at each coin’s address.
- Token lifecycle: `create` on `Coins`; owner can `setMinter`, `transferOwnership`, and `renounceOwnership` (via the token); minters authorized on `Coins` can `mint` through the token.

## Quickstart

1. Deploy to Moccasin’s local network:

```bash
mox run deploy
```

2. Run tests:

```bash
mox test
```

For CLI help, run `mox --help` or see the [Moccasin documentation](https://cyfrin.github.io/moccasin).
