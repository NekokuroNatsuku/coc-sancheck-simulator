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

def roll(dice):
    dice = dice.strip().upper()
    match = re.fullmatch(r'(\\d+)D(\\d+)', dice)
    if match:
        num, sides = map(int, match.groups())
        return np.sum(np.random.randint(1, sides + 1, num))
    else:
        try:
            return int(dice)
        except ValueError:
            st.error(f"無効なダイス表記です: {dice}")
            return 0

def san_check(current_san, success_loss, failure_loss, success_rate=0.5):
    if np.random.rand() < success_rate:
        loss = roll(success_loss)
    else:
        loss = roll(failure_loss)
    return current_san - loss

def simulate_scenario(initial_san, checks, runs=1000):
    breakdown = np.zeros(len(checks))
    san_progress = np.zeros(len(checks))
    san_counts = np.zeros(len(checks))
    final_remaining_san = []

    for _ in range(runs):
        san = initial_san
        for idx, check in enumerate(checks):
            success_loss, failure_loss = check["success"], check["failure"]
            san = san_check(san, success_loss, failure_loss)
            if san > 0:
                san_progress[idx] += san
                san_counts[idx] += 1
            else:
                breakdown[idx] += 1
                break
        else:
            final_remaining_san.append(san)

    avg_san_progress = np.divide(san_progress, san_counts, out=np.zeros_like(san_progress), where=san_counts!=0)
    breakdown_percentage = np.append(breakdown, len(final_remaining_san)) / runs * 100
    avg_final_san = np.mean(final_remaining_san) if final_remaining_san else 0

    return breakdown_percentage, avg_san_progress, avg_final_san

# UI初期化
if 'agreed' not in st.session_state:
    st.session_state.agreed = False
if 'checks' not in st.session_state:
    st.session_state.checks = [{"event": "ゾンビに会う", "success": "0", "failure": "1D3"}]

if not st.session_state.agreed:
    show_terms()
else:
    st.title("🕵️ SANチェック チェッカー")

    for idx, check in enumerate(st.session_state.checks):
        cols = st.columns([3, 1, 1, 1, 1])

        event_name = cols[0].text_input("イベント名", check["event"], key=f"event_{idx}")
        success_loss = cols[1].text_input("成功時減少", check["success"], key=f"s_{idx}")
        failure_loss = cols[2].text_input("失敗時減少", check["failure"], key=f"f_{idx}")

        check.update({"event": event_name, "success": success_loss, "failure": failure_loss})

        if cols[3].button("⬆️", key=f"up_{idx}") and idx > 0:
            st.session_state.checks[idx-1], st.session_state.checks[idx] = st.session_state.checks[idx], st.session_state.checks[idx-1]
            st.rerun()
        if cols[4].button("⬇️", key=f"down_{idx}") and idx < len(st.session_state.checks)-1:
            st.session_state.checks[idx+1], st.session_state.checks[idx] = st.session_state.checks[idx], st.session_state.checks[idx+1]
            st.rerun()
        if cols[4].button("削除", key=f"del_{idx}"):
            st.session_state.checks.pop(idx)
            st.rerun()

    if st.button("SANチェック追加"):
        st.session_state.checks.append({"event": "新しいイベント", "success": "0", "failure": "1D4"})
        st.rerun()

    st.markdown("---")
    if st.button("シミュレーション実行"):
        initial_san_values = list(range(30, 85, 5))
        result_rows = []

        for san in initial_san_values:
            breakdown, avg_san_progress, avg_final_san = simulate_scenario(san, st.session_state.checks)
            row = {"初期SAN": san}
            for idx, check in enumerate(st.session_state.checks):
                row[check["event"]] = f"平均残りSAN値:\\n{avg_san_progress[idx]:.1f}\\nSANロスト率:\\n{breakdown[idx]:.1f}%"
            row["突破率"] = f"{breakdown[-1]:.1f}%"
            row["シナリオ終了時平均残りSAN値"] = f"{avg_final_san:.1f}"
            result_rows.append(row)

        df = pd.DataFrame(result_rows).set_index("初期SAN").T
        st.header("📊 シミュレーション結果")

        def highlight(row):
            return ['background-color: #dddddd; color: black;' if row.name == '突破率' else '' for _ in row]

        st.dataframe(df.style.apply(highlight, axis=1), use_container_width=True)

        st.info("⚠️ 本結果はキーパリングの参考情報です。SNSなど不特定多数の目に触れる場所への公開は利用規約通り禁止となっています。")
"""
