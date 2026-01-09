# app.py - オフライン人狼ゲーム（1端末回し用・騎士まで実装）
import random
import streamlit as st

# =======================
# 初期化
# =======================
def init_game_state():
    st.session_state.phase = "setup"
    st.session_state.num_players = 4
    st.session_state.roles = []
    st.session_state.alive = []
    st.session_state.day_count = 1
    st.session_state.show_index = 0
    st.session_state.night_actions = {
        "wolf_target": None,
        "seer_target": None,
        "guard_target": None,
    }
    st.session_state.seer_done_today = False
    st.session_state.votes = []
    st.session_state.vote_index = 0
    st.session_state.last_night_info = ""
    st.session_state.last_execution = None
    st.session_state.win_side = None

if "phase" not in st.session_state:
    init_game_state()

# =======================
# ユーティリティ関数
# =======================
def get_alive_players():
    return [i for i, alive in enumerate(st.session_state.alive) if alive]

def count_side():
    wolf = sum(1 for i, role in enumerate(st.session_state.roles) 
              if st.session_state.alive[i] and role == "人狼")
    villager = sum(1 for i, role in enumerate(st.session_state.roles) 
                  if st.session_state.alive[i] and role != "人狼")
    return villager, wolf

def check_win():
    villager, wolf = count_side()
    if wolf == 0:
        return "villager"
    if wolf >= villager:
        return "wolf"
    return None

def role_list_for_n_players(n: int):
    if n == 4:
        return ["人狼", "占い師", "騎士", "村人"]
    elif n == 5:
        return ["人狼", "占い師", "騎士", "村人", "村人"]
    elif n == 6:
        return ["人狼", "人狼", "占い師", "騎士", "村人", "村人"]
    elif n == 7:
        return ["人狼", "人狼", "占い師", "騎士", "霊媒師", "村人", "村人"]
    else:  # 8
        return ["人狼", "人狼", "占い師", "騎士", "霊媒師", "村人", "村人", "村人"]

# =======================
# 共通UI
# =======================
st.title("🦊 オフライン人狼ゲーム（1端末用）")
st.caption("4〜8人用 | 人狼・村人・占い師・騎士・霊媒師")

with st.sidebar:
    st.header("📊 ゲーム状況")
    st.write(f"**フェーズ**: {st.session_state.phase}")
    st.write(f"**日数**: {st.session_state.day_count}")
    st.write(f"**生存者**: {sum(st.session_state.alive)}人")
    
    if st.button("🔄 新ゲーム開始", use_container_width=True):
        init_game_state()
        st.rerun()

# =======================
# フェーズ: 設定
# =======================
if st.session_state.phase == "setup":
    st.header("🎮 ゲーム設定")
    
    num = st.number_input("👥 参加人数", min_value=4, max_value=8, 
                         value=st.session_state.num_players)
    st.session_state.num_players = num
    
    st.info("**役職構成**（自動配分）")
    preview_roles = role_list_for_n_players(num)
    st.write("- " + " / ".join(preview_roles))
    
    col1, col2 = st.columns([3,1])
    with col1:
        st.write("**プレイヤーは1〜{}番です**")
        st.caption("※順番は後で確認できます")
    with col2:
        if st.button("🚀 ゲーム開始", use_container_width=True):
            roles = role_list_for_n_players(num)
            random.shuffle(roles)
            st.session_state.roles = roles
            st.session_state.alive = [True] * num
            st.session_state.day_count = 1
            st.session_state.phase = "show_roles"
            st.session_state.show_index = 0
            st.rerun()

# =======================
# フェーズ: 役職確認
# =======================
elif st.session_state.phase == "show_roles":
    st.header("👀 役職確認フェーズ")
    st.info("📱 **端末を順番に回してください**")
    
    idx = st.session_state.show_index
    n = st.session_state.num_players
    
    st.subheader(f"プレイヤー **{idx+1}** 番の方")
    
    if st.button("👁️ 自分の役職を見る", use_container_width=True):
        role = st.session_state.roles[idx]
        st.success(f"**あなたの役職: {role}** 🎭")
    
    if st.button("✅ 次の方へ渡す", use_container_width=True):
        st.session_state.show_index += 1
        if st.session_state.show_index >= n:
            st.session_state.phase = "night"
        st.rerun()

# =======================
# フェーズ: 夜（シンプル版・確実に動く）
# =======================
elif st.session_state.phase == "night":
    st.header(f"🌙 {st.session_state.day_count}日目の夜")
    st.info("🎮 **役職ごとに順番に操作** → 人狼 → 占い師 → 騎士")
    
    alive_players = get_alive_players()
    roles = st.session_state.roles
    
    # 人狼ターン
    st.subheader("🐺 人狼ターン")
    wolves = [i for i in alive_players if roles[i] == "人狼"]
    if wolves and st.session_state.night_actions["wolf_target"] is None:
        targets = [i for i in alive_players if roles[i] != "人狼"]
        target = st.selectbox("襲撃対象を選択", targets,
                             format_func=lambda x: f"👤 プレイヤー {x+1}")
        if st.button("🔪 襲撃実行", use_container_width=True):
            st.session_state.night_actions["wolf_target"] = target
            st.error(f"プレイヤー {target+1} を襲撃対象に決定！")
            st.rerun()
    else:
        st.info("✅ 人狼の行動完了" if st.session_state.night_actions["wolf_target"] else "🐺 生存人狼なし")
    
    # 占い師ターン
    st.subheader("🔮 占い師ターン")
    seers = [i for i in alive_players if roles[i] == "占い師"]
    if seers and not st.session_state.seer_done_today:
        targets = [i for i in alive_players if roles[i] != "占い師"]
        target = st.selectbox("占う対象を選択", targets,
                             format_func=lambda x: f"👤 プレイヤー {x+1}")
        if st.button("🔮 占う！", use_container_width=True):
            result_role = roles[target]
            is_wolf = result_role == "人狼"
            st.session_state.night_actions["seer_target"] = target
            st.session_state.seer_done_today = True
            
            result_msg = f"**プレイヤー {target+1}: {'🦊 人狼！' if is_wolf else '👨‍🌾 村人陣営'}**"
            st.markdown(f"### 🎯 {result_msg}")
            st.balloons()
            st.rerun()
    else:
        st.success("✅ 占い完了" if st.session_state.seer_done_today else "🔮 生存占い師なし")
    
    # 騎士ターン
    st.subheader("🛡️ 騎士ターン")
    guards = [i for i in alive_players if roles[i] == "騎士"]
    if guards and st.session_state.night_actions["guard_target"] is None:
        target = st.selectbox("護衛対象を選択", alive_players,
                             format_func=lambda x: f"👤 プレイヤー {x+1}")
        if st.button("🛡️ 護衛決定", use_container_width=True):
            st.session_state.night_actions["guard_target"] = target
            st.success(f"プレイヤー {target+1} を護衛決定！")
            st.rerun()
    else:
        st.info("✅ 護衛完了" if st.session_state.night_actions["guard_target"] else "🛡️ 生存騎士なし")
    
    # 夜終了判定
    can_end_night = (
        (st.session_state.night_actions["wolf_target"] is not None or len(wolves) == 0) and
        st.session_state.seer_done_today or len(seers) == 0 and
        (st.session_state.night_actions["guard_target"] is not None or len(guards) == 0)
    )
    
    if can_end_night:
        st.subheader("🌅 夜の結果")
        wolf_target = st.session_state.night_actions["wolf_target"]
        guard_target = st.session_state.night_actions["guard_target"]
        
        if wolf_target and guard_target and wolf_target == guard_target:
            st.session_state.last_night_info = f"🛡️ プレイヤー{wolf_target+1}が護衛され無事！"
        elif wolf_target and st.session_state.alive[wolf_target]:
            st.session_state.alive[wolf_target] = False
            st.session_state.last_night_info = f"💀 プレイヤー{wolf_target+1}が死亡"
        else:
            st.session_state.last_night_info = "昨夜は誰も死にませんでした"
        
        st.info(st.session_state.last_night_info)
        
        if st.button("☀️ 朝へ進む", use_container_width=True):
            win = check_win()
            if win:
                st.session_state.win_side = win
                st.session_state.phase = "result"
            else:
                st.session_state.phase = "day_talk"
                st.session_state.day_count += 1
            st.session_state.night_actions = {"wolf_target": None, "seer_target": None, "guard_target": None}
            st.session_state.seer_done_today = False
            st.rerun()

# =======================
# フェーズ: 昼（議論）
# =======================
elif st.session_state.phase == "day_talk":
    st.header(f"☀️ {st.session_state.day_count}日目の昼")
    
    if st.session_state.last_night_info:
        st.error(st.session_state.last_night_info)
    
    alive_str = ", ".join([f"{i+1}" for i in get_alive_players()])
    st.info(f"**生存者**: {alive_str}")
    st.info("💬 **ここで議論を行ってください**")
    
    if st.button("🗳️ 投票フェーズへ", use_container_width=True):
        st.session_state.votes = [None] * st.session_state.num_players
        st.session_state.vote_index = 0
        st.session_state.phase = "vote"
        st.rerun()

# =======================
# フェーズ: 投票
# =======================
elif st.session_state.phase == "vote":
    st.header(f"🗳️ {st.session_state.day_count}日目の投票")
    alive_players = get_alive_players()
    
    idx = st.session_state.vote_index
    if idx >= st.session_state.num_players:
        # 集計
        vote_count = {}
        for i, target in enumerate(st.session_state.votes):
            if target and st.session_state.alive[i]:
                vote_count[target] = vote_count.get(target, 0) + 1
        
        if vote_count:
            max_votes = max(vote_count.values())
            candidates = [p for p, c in vote_count.items() if c == max_votes]
            executed = random.choice(candidates) if len(candidates) > 1 else candidates[0]
            
            if st.session_state.alive[executed]:
                st.session_state.alive[executed] = False
                role = st.session_state.roles[executed]
                st.session_state.last_execution = f"💀 プレイヤー{executed+1}（{role}）が処刑"
                st.error(st.session_state.last_execution)
            else:
                st.info("今回は処刑なし")
        else:
            st.info("投票なし")
        
        if st.button("次へ"):
            win = check_win()
            if win:
                st.session_state.win_side = win
                st.session_state.phase = "result"
            else:
                st.session_state.phase = "night"
            st.rerun()
    else:
        # 投票中
        if not st.session_state.alive[idx]:
            st.info(f"👤 プレイヤー{idx+1}は死亡")
            if st.button("次へ"):
                st.session_state.vote_index += 1
                st.rerun()
        else:
            st.subheader(f"👤 プレイヤー **{idx+1}** の投票")
            targets = [p for p in alive_players if p != idx]
            target = st.selectbox("投票先を選択", targets,
                                 format_func=lambda x: f"👤 プレイヤー {x+1}")
            if st.button("投票確定", use_container_width=True):
                st.session_state.votes[idx] = target
                st.session_state.vote_index += 1
                st.rerun()

# =======================
# フェーズ: 結果
# =======================
elif st.session_state.phase == "result":
    st.header("🏆 ゲーム終了！")
    
    if st.session_state.win_side == "villager":
        st.markdown("## 🎉 **村人陣営の勝利！** 🏆")
    else:
        st.markdown("## 🦊 **人狼陣営の勝利！** 🎭")
    
    st.subheader("📋 最終結果")
    for i, role in enumerate(st.session_state.roles):
        status = "🟢生存" if st.session_state.alive[i] else "🔴死亡"
        st.write(f"**P{i+1}**: {role} {status}")
    
    if st.button("🔄 新しいゲーム", use_container_width=True):
        init_game_state()
        st.rerun()
