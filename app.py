# app.py - オフライン人狼（プレイヤー1→2→3順進行・1端末用）
import random
import streamlit as st

# =======================
# 初期化
# =======================
def init_game_state():
    st.session_state.clear()
    st.session_state.phase = "setup"
    st.session_state.num_players = 4
    st.session_state.roles = []
    st.session_state.alive = []
    st.session_state.day_count = 1
    st.session_state.current_player = 0  # 現在のプレイヤー
    st.session_state.night_actions = {"wolf_target": None, "guard_target": None}
    st.session_state.seer_done_today = False
    st.session_state.votes = []
    st.session_state.vote_index = 0
    st.session_state.last_night_info = ""
    st.session_state.game_log = []

if "phase" not in st.session_state:
    init_game_state()

# =======================
# ユーティリティ
# =======================
def get_alive_players():
    return [i for i, alive in enumerate(st.session_state.alive) if alive]

def count_side():
    wolf = sum(1 for i, r in enumerate(st.session_state.roles) if st.session_state.alive[i] and r == "人狼")
    villager = sum(1 for i, r in enumerate(st.session_state.roles) if st.session_state.alive[i] and r != "人狼")
    return villager, wolf

def check_win():
    v, w = count_side()
    if w == 0: return "villager"
    if w >= v: return "wolf"
    return None

def get_roles_for_players(n):
    if n == 4: return ["人狼", "占い師", "騎士", "村人"]
    if n == 5: return ["人狼", "占い師", "騎士", "村人", "村人"]
    if n == 6: return ["人狼", "人狼", "占い師", "騎士", "村人", "村人"]
    if n == 7: return ["人狼", "人狼", "占い師", "騎士", "霊媒師", "村人", "村人"]
    return ["人狼", "人狼", "占い師", "騎士", "霊媒師", "村人", "村人", "村人"]

# =======================
# UIヘッダー
# =======================
st.title("🦊 人狼ゲーム（1端末回し）")
st.caption("4-8人用 | プレイヤー順進行 | 占い師1日1人制限")

with st.sidebar:
    st.header("📋 状況")
    st.write(f"フェーズ: {st.session_state.phase}")
    st.write(f"日数: {st.session_state.day_count}")
    st.write(f"生存: {sum(st.session_state.alive)}人")
    if st.button("🔄 リセット"):
        init_game_state()
        st.rerun()

# =======================
# フェーズ: 設定
# =======================
if st.session_state.phase == "setup":
    st.header("🎮 ゲーム開始")
    num = st.number_input("人数を選択（4-8人）", 4, 8, 4)
    
    if st.button("🚀 開始", use_container_width=True):
        roles = get_roles_for_players(num)
        random.shuffle(roles)
        st.session_state.num_players = num
        st.session_state.roles = roles
        st.session_state.alive = [True] * num
        st.session_state.day_count = 1
        st.session_state.current_player = 0
        st.session_state.phase = "show_roles"
        st.rerun()
        
    st.info("**役職**: 人狼・村人・占い師・騎士・霊媒師")

# =======================
# フェーズ: 役職確認
# =======================
elif st.session_state.phase == "show_roles":
    st.header("👁️ 役職確認")
    st.info("**プレイヤー1→2→3…順に端末を回してください**")
    
    idx = st.session_state.current_player
    st.subheader(f"プレイヤー {idx+1} 番")
    
    if st.button("役職を見る"):
        role = st.session_state.roles[idx]
        st.success(f"**あなたの役職: {role}** 🎭")
    
    if st.button("次の方へ"):
        st.session_state.current_player += 1
        if st.session_state.current_player >= st.session_state.num_players:
            st.session_state.phase = "night"
            st.session_state.current_player = 0
        st.rerun()

# =======================
# フェーズ: 夜（プレイヤー順）
# =======================
elif st.session_state.phase == "night":
    st.header(f"🌙 {st.session_state.day_count}日目の夜")
    st.info("**プレイヤー1→2→3…順に端末を回してください**")
    
    alive = get_alive_players()
    if not alive:
        st.session_state.phase = "result"
        st.rerun()
    
    current = st.session_state.current_player % len(alive)
    player_idx = alive[current]
    role = st.session_state.roles[player_idx]
    
    st.subheader(f"👤 プレイヤー {player_idx+1} の番")
    st.info(f"**役職: {role}**")
    
    if not st.session_state.alive[player_idx]:
        st.info("死亡済み")
        if st.button("次へ"):
            st.session_state.current_player += 1
            st.rerun()
        st.stop()
    
    # 役職別行動
    if role == "人狼" and st.session_state.night_actions["wolf_target"] is None:
        targets = [i for i in alive if st.session_state.roles[i] != "人狼"]
        target = st.selectbox("襲撃対象", targets, format_func=lambda x: f"P{x+1}")
        if st.button("襲撃決定"):
            st.session_state.night_actions["wolf_target"] = target
            st.error(f"P{target+1} を襲撃決定！")
            st.rerun()
    
    elif role == "占い師" and not st.session_state.seer_done_today:
        targets = [i for i in alive if i != player_idx]
        target = st.selectbox("占う相手", targets, format_func=lambda x: f"P{x+1}")
        if st.button("占う"):
            is_wolf = st.session_state.roles[target] == "人狼"
            st.session_state.seer_done_today = True
            st.session_state.night_actions["seer_target"] = target
            result = "🦊 人狼！" if is_wolf else "👨‍🌾 村人陣営"
            st.markdown(f"### 🎯 **P{target+1}: {result}**")
            st.balloons()
            st.rerun()
    
    elif role == "騎士" and st.session_state.night_actions["guard_target"] is None:
        target = st.selectbox("護衛対象", alive, format_func=lambda x: f"P{x+1}")
        if st.button("護衛決定"):
            st.session_state.night_actions["guard_target"] = target
            st.success(f"P{target+1} を護衛決定！")
            st.rerun()
    
    else:
        st.info("夜の行動なし")
    
    if st.button("次の方へ"):
        st.session_state.current_player += 1
        st.rerun()
    
    # 全員行動後
    if st.session_state.current_player >= len(alive):
        st.subheader("🌅 夜明け")
        
        wolf_t = st.session_state.night_actions["wolf_target"]
        guard_t = st.session_state.night_actions["guard_target"]
        
        if wolf_t and guard_t and wolf_t == guard_t:
            st.session_state.last_night_info = f"🛡️ P{wolf_t+1}が護衛され無事"
        elif wolf_t and st.session_state.alive[wolf_t]:
            st.session_state.alive[wolf_t] = False
            st.session_state.last_night_info = f"💀 P{wolf_t+1}が死亡"
        else:
            st.session_state.last_night_info = "誰も死にませんでした"
        
        st.info(st.session_state.last_night_info)
        
        if st.button("昼へ"):
            win = check_win()
            if win:
                st.session_state.win_side = win
                st.session_state.phase = "result"
            else:
                st.session_state.phase = "day_talk"
                st.session_state.day_count += 1
            st.session_state.night_actions = {"wolf_target": None, "guard_target": None}
            st.session_state.seer_done_today = False
            st.session_state.current_player = 0
            st.rerun()

# =======================
# フェーズ: 昼・投票
# =======================
elif st.session_state.phase == "day_talk":
    st.header(f"☀️ {st.session_state.day_count}日目の昼")
    if st.session_state.last_night_info:
        st.error(st.session_state.last_night_info)
    
    st.info("**議論後、投票フェーズへ**")
    if st.button("🗳️ 投票開始"):
        st.session_state.phase = "vote"
        st.session_state.votes = [None] * st.session_state.num_players
        st.session_state.vote_index = 0
        st.session_state.current_player = 0
        st.rerun()

elif st.session_state.phase == "vote":
    st.header(f"🗳️ 投票フェーズ")
    alive = get_alive_players()
    
    idx = st.session_state.vote_index
    if idx >= st.session_state.num_players:
        # 集計
        vote_count = {}
        for i, t in enumerate(st.session_state.votes):
            if t and st.session_state.alive[i]:
                vote_count[t] = vote_count.get(t, 0) + 1
        
        if vote_count:
            max_v = max(vote_count.values())
            candidates = [p for p, c in vote_count.items() if c == max_v]
            executed = random.choice(candidates) if len(candidates) > 1 else candidates[0]
            
            if st.session_state.alive[executed]:
                st.session_state.alive[executed] = False
                role = st.session_state.roles[executed]
                st.error(f"💀 P{executed+1}（{role}）が処刑されました")
        else:
            st.info("今回は処刑なし")
        
        if st.button("次へ"):
            win = check_win()
            if win:
                st.session_state.win_side = win
                st.session_state.phase = "result"
            else:
                st.session_state.phase = "night"
            st.session_state.current_player = 0
            st.rerun()
    else:
        player_idx = idx
        st.subheader(f"P{player_idx+1} の投票")
        
        if not st.session_state.alive[player_idx]:
            st.info("死亡")
            if st.button("次へ"):
                st.session_state.vote_index += 1
                st.rerun()
        else:
            targets = [p for p in alive if p != player_idx]
            target = st.selectbox("投票先", targets, format_func=lambda x: f"P{x+1}")
            if st.button("投票"):
                st.session_state.votes[player_idx] = target
                st.session_state.vote_index += 1
                st.rerun()

# =======================
# フェーズ: 結果
# =======================
elif st.session_state.phase == "result":
    st.header("🏆 ゲーム終了！")
    
    if st.session_state.win_side == "villager":
        st.success("🎉 村人陣営勝利！")
    else:
        st.error("🦊 人狼陣営勝利！")
    
    st.subheader("最終結果")
    for i, role in enumerate(st.session_state.roles):
        status = "🟢生存" if st.session_state.alive[i] else "🔴死亡"
        st.write(f"P{i+1}: {role} {status}")
    
    if st.button("🔄 新ゲーム", use_container_width=True):
        init_game_state()
        st.rerun()
