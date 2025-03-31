import streamlit as st
import numpy as np
import pandas as pd
import re

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
        st.experimental_rerun()

# ダイスロール関数（例：1D6）
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
            if check == "branch":
                continue
            success_loss, failure_loss = check
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

# Streamlit UI
st.set_page_config(layout="wide")

# 利用規約確認
if 'agreed' not in st.session_state:
    st.session_state.agreed = False

if not st.session_state.agreed:
    show_terms()
else:
    st.title("🕵️ CoC TRPG - SANチェック補佐シミュレーター")

    st.sidebar.header("シナリオのSANチェック設定")

    if 'checks' not in st.session_state:
        st.session_state.checks = [("0", "1D4")]

    def add_check():
        st.session_state.checks.append(("0", "1D4"))

    def add_branch():
        branch_count = st.sidebar.number_input("分岐数", 2, 5, 2, key="branch_count")
        st.session_state.checks.append("branch")
        for _ in range(branch_count):
            st.session_state.checks.append(("0", "1D4"))

    def remove_check(index):
        st.session_state.checks.pop(index)

    def move_up(index):
        if index > 0:
            st.session_state.checks[index], st.session_state.checks[index-1] = st.session_state.checks[index-1], st.session_state.checks[index]

    def move_down(index):
        if index < len(st.session_state.checks) - 1:
            st.session_state.checks[index], st.session_state.checks[index+1] = st.session_state.checks[index+1], st.session_state.checks[index]

    for idx, check in enumerate(st.session_state.checks):
        if check == "branch":
            st.sidebar.markdown("--- 以下ルート分岐 ---")
            continue

        success_loss, failure_loss = check
        st.sidebar.subheader(f"チェック #{idx+1}")
        success_loss = st.sidebar.text_input(f"成功時のSAN減少 ({idx+1})", success_loss, key=f"s_{idx}")
        failure_loss = st.sidebar.text_input(f"失敗時のSAN減少 ({idx+1})", failure_loss, key=f"f_{idx}")
        st.session_state.checks[idx] = (success_loss, failure_loss)

        col1, col2, col3 = st.sidebar.columns([1,1,1])
        with col1:
            if st.button("⬆️", key=f"up_{idx}"):
                move_up(idx)
                st.experimental_rerun()
        with col2:
            if st.button("⬇️", key=f"down_{idx}"):
                move_down(idx)
                st.experimental_rerun()
        with col3:
            if st.button(f"削除", key=f"del_{idx}"):
                remove_check(idx)
                st.experimental_rerun()

    col_add, col_branch = st.sidebar.columns(2)
    with col_add:
        st.button("SANチェック追加", on_click=add_check)
    with col_branch:
        st.button("ルート分岐追加", on_click=add_branch)

    if st.sidebar.button("シミュレーション実行"):
        initial_san_values = list(range(30, 95, 5))
        results = []

        for san in initial_san_values:
            breakdown, avg_rem, var_rem = simulate_scenario(san, st.session_state.checks)
            results.append({
                "初期SAN値": san,
                **{f"#{idx+1}脱落率(%)": f"{breakdown[idx]:.1f}" for idx in range(len(st.session_state.checks)) if st.session_state.checks[idx] != "branch"},
                "突破率(%)": f"{breakdown[-1]:.1f}",
                "平均残SAN": f"{avg_rem:.1f}",
                "残SAN分散": f"{var_rem:.1f}"
            })

        df = pd.DataFrame(results)
        st.write("### 🧠 シミュレーション結果")
        st.dataframe(df, use_container_width=True)

        st.info("⚠️ 本結果はキーパリングの参考情報です。SNSなど不特定多数の目に触れる場所への公開は利用規約通り禁止となっています。")
