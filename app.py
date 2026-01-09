# app.py - 人狼ゲーム（プレイヤー順進行・2日目対応版）
import random
import streamlit as st

# =======================
# 初期化（完全版）
# =======================
def init_game_state():
    st.session_state.clear()
    st.session_state.phase = "setup"
    st.session_state.num_players = 4
    st.session_state.roles = []
    st.session_state.alive = []
    st.session_state.day_count = 1
    st.session_state.current_player = 0
    st.session_state.night_actions = {"wolf_target": None, "guard_target": None, "seer_target": None}
    st.session_state.seer_done_today = False
    st.session_state.votes = []
    st.session_state.vote_index = 0
    st.session_state.last_night_info = ""
    st.session_state.game_winner = None

if "phase" not in st.session_state:
    init_game_state()

# =======================
# ユーティリティ関数
# =======================
def get_alive_players():
    if not st.session_state.alive:
        return []
    return [i for i, alive in enumerate(st.session_state.alive) if alive]

def count_side():
    if not st.session_state.roles or not st.session_state.alive:
        return 0, 0
    wolf = sum(1 for i, r in enumerate(st.session_state.roles) if st.session_state.alive[i] and r == "人狼")
    villager = sum(1 for i, r in enumerate(st.session_state.roles) if st.session_state.alive[i] and r != "人狼")
    return villager, wolf

def check_win():
    v, w = count_side()
    if w == 0: 
        return "villager"
    if w >= v: 
        return "wolf"
    return None

def get_roles_for_players(n):
    roles = {
        4: ["人狼", "占い師", "騎士", "村人"],
        5: ["人狼", "占い師", "騎士", "村人", "村人"],
        6: ["人狼", "人狼", "占い師", "騎士", "村人", "村人"],
        7: ["人狼", "人狼", "占い師", "騎士", "霊媒師", "村人", "村人"],
        8: ["人狼", "人狼", "占い師", "騎士", "霊媒師", "村人", "村人", "村人"]
    }
    return roles.get(n, roles[8])

# =======================
# メインUI
# =======================
st.title("🦊 人狼ゲーム（1端末・プレイヤー順）")
st.caption("4-8人 | 占い師1日1人制限 | 完全オフライン")

with st.sidebar:
    st.header("📊 ゲーム状況")
    st.write(f"フェーズ: {st.session_state.phase}")
    st.write(f"日数: Day {st.session_state.day_count}")
    st.write(f"生存者: {sum(st.session_state.alive) if st.session_state.alive else 0}/"
             f"{st.session_state.num_players if st.session_state.num_players else 0}")
    if st.button("🔄 新規ゲーム"):
        init_game_state()
        st.rerun()

# =======================
# フェーズ1: 設定
# =======================
if st.session_state.phase == "setup":
    st.header("🎮 ゲーム設定")
    num = st.number_input("👥 人数を選択（4-8人）", 4, 8, 4)
    
    st.subheader("📋 役職構成（自動配分）")
    roles = get_roles_for_players(num)
    role_count = {}
    for role in roles:
        role_count[role] = role_count.get(role, 0) + 1
    for role, count in role_count.items():
        st.write(f"• {role}: {count}人")
    
    if st.button("🚀 役職配布・開始", use_container_width=True):
        random.shuffle(roles)
        st.session_state.num_players = num
        st.session_state.roles = roles
        st.session_state.alive = [True] * num
        st.session_state.day_count = 1
        st.session_state.current_player = 0
        st.session_state.phase = "show_roles"
        st.rerun()

# =======================
# フェーズ2: 役職確認
# =======================
elif st.session_state.phase == "show_roles":
    st.header("👁️ 役職確認フェーズ")
    st.info("📱 **プレイヤー1→2→3…順に端末を回してください**")
    
    idx = st.session_state.current_player
    st.subheader(f"👤 プレイヤー {idx+1} 番の方")
    
    if st.button("🔍 自分の役職を見る", use_container_width=True):
        role = st.session_state.roles[idx]
        st.markdown(f"### 🎭 **あなたの役職: {role}**")
        st.balloons()
    
    if st.button("✅ 確認完了・次へ", use_container_width=True):
        st.session_state.current_player += 1
        if st.session_state.current_player >= st.session_state.num_players:
            st.session_state.current_player = 0
            st.session_state.phase = "night"
        st.rerun()

# =======================
# フェーズ3: 夜（風船なし・役職非表示＋占い結果確認）
# =======================
elif st.session_state.phase == "night":
    st.header(f"🌙 {st.session_state.day_count}日目の夜")
    st.info("🔄 **プレイヤー1→2→3…順に端末を回してください**")
    
    alive_players = get_alive_players()
    if not alive_players:
        st.session_state.phase = "result"
        st.rerun()
    
    # 生存者リストから現在プレイヤーを取得
    current_idx = st.session_state.current_player % len(alive_players)
    player_idx = alive_players[current_idx]
    role = st.session_state.roles[player_idx]
    
    st.subheader(f"👤 **プレイヤー {player_idx+1}** の行動")
    st.info(f"🎭 **役職: {role}**")
    
    # 死亡チェック
    if not st.session_state.alive[player_idx]:
        st.warning("❌ 死亡済みのためスキップ")
        if st.button("⏭️ 次の方へ"):
            st.session_state.current_player += 1
            st.rerun()
        st.stop()
    
    # === 占い師結果確認フラグ ===
    if "seer_result_showing" not in st.session_state:
        st.session_state.seer_result_showing = False
        st.session_state.seer_result = None
    
    # === 役職別行動 ===
    action_done = False
    
    # 人狼（役職非表示）
    if role == "人狼" and st.session_state.night_actions["wolf_target"] is None:
        targets = [i for i in alive_players if st.session_state.roles[i] != "人狼"]
        if targets:
            target = st.selectbox("🐺 襲撃対象を選択", targets, 
                                format_func=lambda x: f"P{x+1}")  # 役職非表示
            if st.button("🔪 襲撃実行", use_container_width=True):
                st.session_state.night_actions["wolf_target"] = target
                st.error(f"✅ P{target+1} を襲撃決定！")
                st.rerun()
        action_done = True
    
    # 占い師（確認ボタン版・風船なし）
    elif role == "占い師" and not st.session_state.seer_done_today:
        targets = [i for i in alive_players if i != player_idx]
        if targets:
            target = st.selectbox("🔮 占う相手を選択", targets, 
                                format_func=lambda x: f"P{x+1}")
            if st.button("🔮 占う！", use_container_width=True):
                is_wolf = st.session_state.roles[target] == "人狼"
                st.session_state.seer_done_today = True
                st.session_state.night_actions["seer_target"] = target
                st.session_state.seer_result = {
                    "target": target,
                    "is_wolf": is_wolf
                }
                st.session_state.seer_result_showing = True
                st.rerun()
        action_done = True
    
    # 占い師結果確認画面（風船なし）
    elif st.session_state.seer_result_showing and role == "占い師":
        res = st.session_state.seer_result
        result_text = f"P{res['target']+1} → " + \
                     ("🦊 **人狼です！**" if res['is_wolf'] else "👨‍🌾 **村人陣営です**")
        st.markdown(f"### 🔮 **占い結果**")
        st.markdown(f"#### 🎯 **{result_text}**")
        
        if st.button("✅ 結果を確認しました", use_container_width=True):
            st.session_state.seer_result_showing = False
            st.rerun()
        st.stop()
    
    # 騎士（役職非表示）
    elif role == "騎士" and st.session_state.night_actions["guard_target"] is None:
        target = st.selectbox("🛡️ 護衛対象を選択", alive_players, 
                            format_func=lambda x: f"P{x+1}")
        if st.button("🛡️ 護衛実行", use_container_width=True):
            st.session_state.night_actions["guard_target"] = target
            st.success(f"✅ P{target+1} を護衛決定！")
            st.rerun()
        action_done = True
    
    # その他
    else:
        st.info("😴 **この役職に夜の行動はありません**")
        action_done = True
    
    # 次へボタン
    if st.bu


# =======================
# フェーズ4: 昼・議論
# =======================
elif st.session_state.phase == "day_talk":
    st.header(f"☀️ {st.session_state.day_count}日目の昼")
    if st.session_state.last_night_info:
        st.error(f"🌙 **昨夜**: {st.session_state.last_night_info}")
    
    alive_str = ", ".join([f"P{i+1}" for i in get_alive_players()])
    st.info(f"👥 **生存者**: {alive_str}")
    st.info("💬 **ここで議論を行ってください**")
    
    if st.button("🗳️ 投票フェーズ開始", use_container_width=True):
        st.session_state.phase = "vote"
        st.session_state.votes = [None] * st.session_state.num_players
        st.session_state.vote_index = 0
        st.session_state.current_player = 0
        st.rerun()

# =======================
# フェーズ5: 投票
# =======================
elif st.session_state.phase == "vote":
    st.header(f"🗳️ {st.session_state.day_count}日目の投票")
    alive_players = get_alive_players()
    
    idx = st.session_state.vote_index
    if idx >= st.session_state.num_players:
        # 投票集計
        vote_count = {}
        for i, target in enumerate(st.session_state.votes):
            if target is not None and st.session_state.alive[i]:
                vote_count[target] = vote_count.get(target, 0) + 1
        
        st.subheader("📊 投票結果")
        if vote_count:
            max_votes = max(vote_count.values())
            candidates = [p for p, c in vote_count.items() if c == max_votes]
            executed = random.choice(candidates) if len(candidates) > 1 else candidates[0]
            
            if st.session_state.alive[executed]:
                st.session_state.alive[executed] = False
                role = st.session_state.roles[executed]
                st.session_state.last_night_info = f"💀 P{executed+1}（{role}）が処刑されました"
                st.error(st.session_state.last_night_info)
            else:
                st.info("今回は処刑なし")
        else:
            st.info("有効投票なし")
        
        if st.button("🌙 夜へ進む", use_container_width=True):
            winner = check_win()
            if winner:
                st.session_state.game_winner = winner
                st.session_state.phase = "result"
            else:
                st.session_state.phase = "night"
                st.session_state.day_count += 1
                st.session_state.current_player = 0
                st.session_state.night_actions = {"wolf_target": None, "guard_target": None, "seer_target": None}
                st.session_state.seer_done_today = False
            st.rerun()
    else:
        # 投票中
        player_idx = idx
        st.subheader(f"👤 P{player_idx+1} の投票ターン")
        
        if not st.session_state.alive[player_idx]:
            st.info("❌ 死亡済みのためスキップ")
            if st.button("次へ"):
                st.session_state.vote_index += 1
                st.rerun()
        else:
            targets = [p for p in alive_players if p != player_idx]
            target = st.selectbox("投票先を選択", targets, format_func=lambda x: f"P{x+1}")
            if st.button("✅ 投票確定", use_container_width=True):
                st.session_state.votes[player_idx] = target
                st.session_state.vote_index += 1
                st.rerun()

# =======================
# フェーズ6: 結果
# =======================
elif st.session_state.phase == "result":
    st.header("🏆 **ゲーム終了！**")
    
    if st.session_state.game_winner == "villager":
        st.markdown("### 🎉 **村人陣営の勝利！** 🏆")
    else:
        st.markdown("### 🦊 **人狼陣営の勝利！** 🎭")
    
    st.subheader("📋 全員の役職と結果")
    for i, role in enumerate(st.session_state.roles):
        status = "🟢 生存" if st.session_state.alive[i] else "🔴 死亡"
        st.write(f"**P{i+1}**: {role} - {status}")
    
    if st.button("🔄 新しいゲームを開始", use_container_width=True):
        init_game_state()
        st.rerun()
