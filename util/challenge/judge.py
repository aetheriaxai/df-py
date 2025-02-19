# adapted from https://github.com/oceanprotocol/predict-eth-judge/blob/main/pej

import os
from calendar import WEDNESDAY
from datetime import datetime, timedelta, timezone
from typing import List, Tuple

import ccxt
from brownie.network import accounts
from enforce_typing import enforce_types
import gql
from gql.transport.aiohttp import AIOHTTPTransport
import numpy as np

from util import crypto, oceanutil
from util.challenge import helpers

# this is the address that contestants encrypt their data to, and send to
JUDGE_ADDRESS = "0xA54ABd42b11B7C97538CAD7C6A2820419ddF703E"

# for testing dftool
DFTOOL_TEST_FAKE_CSVDIR = "fakedir_dftool"
DFTOOL_TEST_FAKE_CHALLENGE_DATA = (
    ["0xfrom1", "0xfrom2"],
    ["0xnft1", "0xnft2"],
    [0.2, 1.0],
)


def _get_gql_client():
    # note: only supports mumbai right now

    prefix = "https://v4.subgraph.mumbai.oceanprotocol.com"
    url = f"{prefix}/subgraphs/name/oceanprotocol/ocean-subgraph"
    transport = AIOHTTPTransport(url=url)

    client = gql.Client(transport=transport, fetch_schema_from_transport=True)
    return client


@enforce_types
def _get_txs(deadline_dt) -> list:
    # https://github.com/oceanprotocol/ocean-subgraph/blob/main/schema.graphql
    a_week_before_deadline = deadline_dt - timedelta(weeks=1)

    query_s = f"""
{{nftTransferHistories(
    where: {{
             newOwner: "{JUDGE_ADDRESS.lower()}",
             timestamp_gt: {a_week_before_deadline.timestamp()},
             timestamp_lte: {deadline_dt.timestamp()}
            }}
)
    {{
        id,
        timestamp,
        nft {{
            id
        }},
        oldOwner {{
            id
        }},
        newOwner {{
            id
        }}
     }}
}}"""

    query = gql.gql(query_s)
    gql_client = _get_gql_client()
    result = gql_client.execute(query)
    txs = result["nftTransferHistories"]

    return txs


@enforce_types
def _date(tx):
    ut = int(tx["timestamp"])
    return helpers.ut_to_dt(ut)


@enforce_types
def _nft_addr(tx):
    return tx["nft"]["id"]


@enforce_types
def _from_addr(tx):
    return tx["oldOwner"]["id"]


@enforce_types
def _nft_addr_to_pred_vals(nft_addr: str, judge_acct) -> List[float]:
    nft = oceanutil.getDataNFT(nft_addr)
    pred_vals_str_enc = oceanutil.getDataField(nft, "predictions")
    try:
        pred_vals_str = crypto.asym_decrypt(pred_vals_str_enc, judge_acct.private_key)
        pred_vals = [float(s) for s in pred_vals_str[1:-1].split(",")]
    except:  # pylint: disable=W0702
        return []

    return pred_vals


@enforce_types
def _get_cex_vals(deadline_dt):
    now = datetime.now(timezone.utc)
    newest_cex_dt = deadline_dt + timedelta(minutes=(1 + 12 * 5))
    print("get_cex_vals: start")
    print(f"  now           = {now} (UTC)")
    print(f"  deadline_dt   = {deadline_dt} (UTC)")
    print(f"  newest_cex_dt = {newest_cex_dt} (UTC)")
    assert deadline_dt.tzinfo == timezone.utc, "must be in UTC"
    assert deadline_dt <= now, "deadline must be past"
    assert newest_cex_dt <= now, "cex vals must be past"

    start_dt = deadline_dt + timedelta(minutes=1)
    target_dts = [
        start_dt + timedelta(minutes=_min) for _min in range(5, 5 + 12 * 5, 5)
    ]
    target_uts = [helpers.dt_to_ut(dt) for dt in target_dts]
    helpers.print_datetime_info("target times", target_uts)

    kraken = ccxt.kraken()
    from_dt_str = kraken.parse8601(deadline_dt.strftime("%Y-%m-%d %H:%M:00"))
    cex_x = kraken.fetch_ohlcv("ETH/USDT", "5m", since=from_dt_str, limit=500)
    allcex_uts = [xi[0] / 1000 for xi in cex_x]
    allcex_vals = [xi[4] for xi in cex_x]
    helpers.print_datetime_info("CEX data info", allcex_uts)

    cex_vals = helpers.filter_to_target_uts(target_uts, allcex_uts, allcex_vals)
    print(f"  cex ETH price is ${cex_vals[0]} at target time 0")
    print(f"  cex_vals: {cex_vals}")

    print("get_cex_vals: done")
    return cex_vals


@enforce_types
def parse_deadline_str(deadline_str: str) -> datetime:
    """
    @arguments
      deadline_str - submission deadline
        Format: YYYY-MM-DD_HOUR:MIN in UTC, or None (use most recent Wed 23:59)
        Example for Round 5: 2023-05-03_23:59
      judge_acct -- brownie account

    @return
      deadline_dt -- datetime object, in UTC
    """
    if deadline_str == "None":
        today = datetime.now(timezone.utc)
        today = today.replace(hour=0, minute=0, second=0, microsecond=0)

        offset = (today.weekday() - WEDNESDAY) % 7
        prev_wed = today - timedelta(days=offset)
        deadline_dt = prev_wed.replace(hour=23, minute=59, second=0, microsecond=0)
    else:
        deadline_dt = datetime.strptime(deadline_str, "%Y-%m-%d_%H:%M")
        deadline_dt = deadline_dt.replace(tzinfo=timezone.utc)

    assert deadline_dt.tzinfo == timezone.utc, "must be in UTC"
    return deadline_dt


@enforce_types
def print_results(challenge_data):
    (from_addrs, nft_addrs, nmses) = challenge_data
    assert len(from_addrs) == len(nft_addrs) == len(nmses)
    assert nmses == sorted(nmses), "should be sorted by lowest-nmse first"

    print("\n-------------")
    print("Summary:")
    print("-------------")

    print(f"\n{len(nmses)} entries, lowest-nmse first:")
    print("-------------")
    n = len(nmses)
    for i in range(n):
        rank = i + 1
        print(
            f"#{rank:2}. NMSE: {nmses[i]:.3e}, from: {from_addrs[i]}"
            f", nft: {nft_addrs[i]}"
        )

    print("\npej: Done")


@enforce_types
def _keep_youngest_entry_per_competitor(txs: list, nmses: list) -> list:
    """For each from_addr with >1 entry, make all nmses 1.0 except youngest"""
    print()
    print("Keep-youngest: begin")
    from_addrs = [_from_addr(tx) for tx in txs]
    for from_addr in set(from_addrs):
        I = [
            i
            for i, cand_from_addr in enumerate(from_addrs)
            if cand_from_addr == from_addr
        ]
        if len(I) == 1:
            continue
        Ip1 = [i + 1 for i in I]
        print()
        print(f"  NFTs #{Ip1} all come {from_addrs[I[0]]}")

        dates = [_date(txs[i]) for i in I]
        youngest_j = np.argmax(dates)
        print(f"  Youngest is #{Ip1[youngest_j]}, at {dates[youngest_j]}")

        for j, i in enumerate(I):
            if j != youngest_j:
                nmses[I[j]] = 1.0
                print(f"  Non-youngest #{[Ip1[j]]}, at {dates[j]} gets nmse = 1.0")
    print()
    print("Keep-youngest: done")

    return nmses


@enforce_types
def get_judge_acct():
    judge_private_key = os.getenv("JUDGE_PRIVATE_KEY")
    assert judge_private_key, "need to set envvar JUDGE_PRIVATE_KEY"

    judge_acct = accounts.add(judge_private_key)
    assert judge_acct.address.lower() == JUDGE_ADDRESS.lower(), (
        f"JUDGE_PRIVATE_KEY is wrong, it must give address={JUDGE_ADDRESS}"
        "\nGet it at private repo https://github.com/oceanprotocol/private-keys"
    )

    return judge_acct


@enforce_types
def get_challenge_data(
    deadline_dt: datetime, judge_acct
) -> Tuple[List[str], List[str], list]:
    """
    @arguments
      deadline_dt -- submission deadline, in UTC
      judge_acct -- brownie account, must have JUDGE_ADDR

    @return -- three lists, all ordered with lowest nmse first
      from_addrs -- list of [tx_i] : from_addr_str
      nft_addrs -- list of [tx_i] : nft_addr_str
      nmses -- list of [tx_i] : nmse_float_or_int
    """
    print(f"get_challenge_data: start. deadline_dt={deadline_dt}")
    assert deadline_dt.tzinfo == timezone.utc, "deadline must be in UTC"
    assert judge_acct.address.lower() == JUDGE_ADDRESS.lower()

    cex_vals = _get_cex_vals(deadline_dt)

    txs = _get_txs(deadline_dt)

    nft_addrs = [_nft_addr(tx) for tx in txs]
    from_addrs = [_from_addr(tx) for tx in txs]

    n = len(nft_addrs)
    nmses = [1.0] * n  # fill this in
    for i in range(n):
        tx, nft_addr, from_addr = txs[i], nft_addrs[i], from_addrs[i]

        print("=" * 60)
        print(f"NFT #{i+1}/{n}: Begin.")
        print(f"date = {_date(tx)}")
        print(f"from_addr = {from_addr}")
        print(f"nft_addr = {nft_addr}")

        # get predicted ETH values
        pred_vals = _nft_addr_to_pred_vals(nft_addr, judge_acct)  # main call
        print(f"pred_vals: {pred_vals}")

        if len(pred_vals) != len(cex_vals):
            nmses[i] = 1.0
            print("nmse = 1.0 because improper # pred_vals")
        else:
            nmses[i] = helpers.calc_nmse(cex_vals, pred_vals)
            # plot_prices(cex_vals, pred_vals)
            print(f"nmse = {nmses[i]:.3e}. (May become 1.0, eg if duplicates)")

        print(f"NFT #{i+1}/{n}: Done")

    # For each from_addr with >1 entry, make all nmses 1.0 except youngest
    nmses = _keep_youngest_entry_per_competitor(txs, nmses)

    # Sort results for lowest-nmse first
    I = np.argsort(nmses)
    from_addrs = [from_addrs[i] for i in I]
    nft_addrs = [nft_addrs[i] for i in I]
    nmses = [nmses[i] for i in I]

    # print
    challenge_data = (from_addrs, nft_addrs, nmses)
    print_results(challenge_data)

    # return
    print(f"get_challenge_data(): done. {len(nmses)} results")
    return challenge_data
