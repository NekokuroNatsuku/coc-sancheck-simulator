import streamlit as st
import numpy as np
import pandas as pd
import re

st.set_page_config(layout="wide")

# 利用規約表示用の関数
def show_terms():
    st.title("📜 利用規約 / Terms of Use")
    st.write("""
    本アプリケーションはクトゥルフ神話TRPGのキーパリング補助を目的としたシミュレーターツールです。

    - 本アプリで得た情報は、ご自身のキーパリングのための参考情報としてのみご使用ください。
    - 出力結果をSNSなど不特定多数の目に触れる場所へ公開、共有、転載することを禁止します。
    - 本アプリの使用によるトラブルについて、開発者は一切の責任を負いません。

    上記の内容に同意する場合のみ、アプリケーションをご利用ください。

    ---

    This application is a simulator designed to assist Keepers of Call of Cthulhu TRPG.

    - Information obtained from this app should be used solely as reference material for your own Keepering.
    - You are prohibited from publicly sharing, distributing, or reposting the results on SNS or any other publicly accessible places.
    - The developer assumes no responsibility for any troubles arising from the use of this application.

    Please use the application only if you agree to the above terms.
    """)
    if st.button("同意する / Agree"):
        st.session_state.agreed = True
        st.rerun()

# ダイスロール関数
def roll(dice):
    match = re.match(r'(\d+)D(\d+)', dice.upper())
    if match:
        num, sides = map(int, match.groups())
        return np.sum(np.random.randint(1, sides+1, num))
    else:
        return int(dice)

# SANチェック関数
def san_check(current_san, success_loss, failure_loss, success_rate=0.5):
    if np.random.rand() < success_rate:
        loss = roll(success_loss)
    else:
        loss = roll(failure_loss)
    return current_san - loss

# シナリオシミュレーション関数
def simulate_scenario(initial_san, checks, runs=1000):
    breakdown = np.zeros(len(checks) + 1)
    remaining_san = []

    for _ in range(runs):
        san = initial_san
        for idx, check in enumerate(checks):
            if isinstance(check, dict) and check.get("branch"):
                continue
            success_loss, failure_loss = check["success"], check["failure"]
            san = san_check(san, success_loss, failure_loss)
            if san <= 0:
                breakdown[idx] += 1
                break
        else:
            breakdown[-1] += 1
            remaining_san.append(san)

    avg_remaining = np.mean(remaining_san) if remaining_san else 0
    var_remaining = np.var(remaining_san) if remaining_san else 0

    return breakdown / runs * 100, avg_remaining, var_remaining

# UI初期化
if 'agreed' not in st.session_state:
    st.session_state.agreed = False
if 'checks' not in st.session_state:
    st.session_state.checks = [{"event": "ゾンビに会う", "success": "0", "failure": "1D3"}]

if not st.session_state.agreed:
    show_terms()
else:
    st.title("🕵️ SANチェック チェッカー")

    initial_san_values = list(range(30, 85, 5))
    columns = ["イベント"] + [str(san) for san in initial_san_values]

    col_widths = [2] + [1 for _ in initial_san_values]
    header_cols = st.columns(col_widths)
    for col, title in zip(header_cols, columns):
        col.markdown(f"### {title}")

    for idx, check in enumerate(st.session_state.checks):
        cols = st.columns(col_widths)

        if isinstance(check, dict) and check.get("branch"):
            cols[0].markdown("--- 以下ルート分岐 ---")
            branches = check["branch"]
            branch_cols = st.columns(len(branches))
            for b_idx, branch in enumerate(branches):
                with branch_cols[b_idx]:
                    branch_event = st.text_input(f"分岐名 ({idx+1}-{b_idx+1})", branch["event"], key=f"branch_event_{idx}_{b_idx}")
                    branch_success = st.text_input(f"成功時SAN減少 ({idx+1}-{b_idx+1})", branch["success"], key=f"branch_success_{idx}_{b_idx}")
                    branch_failure = st.text_input(f"失敗時SAN減少 ({idx+1}-{b_idx+1})", branch["failure"], key=f"branch_failure_{idx}_{b_idx}")
                    branch.update({"event": branch_event, "success": branch_success, "failure": branch_failure})
        else:
            event_name = cols[0].text_input(f"イベント名 ({idx+1})", check["event"], key=f"event_{idx}")
            success_loss = cols[0].text_input(f"成功時のSAN減少 ({idx+1})", check["success"], key=f"s_{idx}")
            failure_loss = cols[0].text_input(f"失敗時のSAN減少 ({idx+1})", check["failure"], key=f"f_{idx}")
            check.update({"event": event_name, "success": success_loss, "failure": failure_loss})

    if st.button("SANチェック追加"):
        st.session_state.checks.append({"event": "新しいイベント", "success": "0", "failure": "1D4"})
        st.rerun()

    if st.button("ルート分岐追加"):
        branch_count = 2  # default分岐数
        branches = [{"event": f"分岐{i+1}", "success": "0", "failure": "1D4"} for i in range(branch_count)]
        st.session_state.checks.append({"event": "ルート分岐", "branch": branches})
        st.rerun()

    st.markdown("---")
    if st.button("シミュレーション実行"):
        st.header("📊 シミュレーション結果")
        st.info("⚠️ 本結果はキーパリングの参考情報です。SNSなど不特定多数の目に触れる場所への公開は利用規約通り禁止となっています。")
