# app.py
import random
import streamlit as st

# =======================
# 初期化ヘルパー
# =======================
def init_game_state():
    st.session_state.phase = "setup"  # setup, show_roles, night, day_talk, vote, result
    st.session_state.num_players = 4
    st.session_state.roles = []       # 各プレイヤーの役職
    st.session_state.alive = []       # 各プレイヤーが生きているか
    st.session_state.day_count = 1
    st.session_state.show_index = 0   # 役職確認や投票で使うインデックス
    st.session_state.night_step = "wolf"  # wolf -> seer -> guard -> resolve
    st.session_state.night_actions = {
        "wolf_target": None,
        "seer_target": None,
        "guard_target": None,
    }
    st.session_state.vote_index = 0
    st.session_state.votes = []           # 投票先（長さ=人数）
    st.session_state.last_night_info = "" # 「昨夜の出来事」
    st.session_state.last_execution = None
    st.session_state.win_side = None      # "villager", "wolf", "draw" など

if "phase" not in st.session_state:
    init_game_state()

# =======================
# ユーティリティ
# =======================
def get_alive_players():
    return [i for i, alive in enumerate(st.session_state.alive) if alive]

def count_side():
    # 村人陣営：村人・占い師・騎士・霊媒師
    # 人狼陣営：人狼
    wolf = 0
    villager = 0
    for i, role in enumerate(st.session_state.roles):
        if not st.session_state.alive[i]:
            continue
        if role == "人狼":
            wolf += 1
        else:
            villager += 1
    return villager, wolf

def check_win():
    villager, wolf = count_side()
    if wolf == 0:
        return "villager"
    if wolf >= villager:
        return "wolf"
    return None

def role_list_for_n_players(n: int):
    """
    人数に合わせて役職構成を決める簡易ルール。
    必要に応じてここを調整してください。
    """
    if n == 4:
        base = ["人狼", "占い師", "騎士", "村人"]
    elif n == 5:
        base = ["人狼", "占い師", "騎士", "村人", "村人"]
    elif n == 6:
        base = ["人狼", "人狼", "占い師", "騎士", "村人", "村人"]
    elif n == 7:
        base = ["人狼", "人狼", "占い師", "騎士", "霊媒師", "村人", "村人"]
    else:  # n == 8
        base = ["人狼", "人狼", "占い師", "騎士", "霊媒師", "村人", "村人", "村人"]
    return base

# =======================
# 画面共通のヘッダ
# =======================
st.title("オフライン人狼（1端末用）")

with st.sidebar:
    st.header("ゲーム情報")
    st.write(f"フェーズ: {st.session_state.phase}")
    st.write(f"日数: {st.session_state.day_count}")
    if st.button("ゲームをリセット"):
        init_game_state()
        st.experimental_rerun()

# =======================
# フェーズ: 設定
# =======================
if st.session_state.phase == "setup":
    st.header("ゲーム設定")

    num = st.number_input(
        "人数を選んでください（4〜8人）",
        min_value=4,
        max_value=8,
        value=st.session_state.num_players,
        step=1,
    )
    st.session_state.num_players = num

    st.write("今回使う基本役職：")
    st.write("人狼・村人・占い師・騎士・霊媒師（人数に応じて自動で配分）")

    if st.button("役職を配布してゲーム開始"):
        n = st.session_state.num_players
        roles = role_list_for_n_players(n)
        random.shuffle(roles)
        st.session_state.roles = roles
        st.session_state.alive = [True] * n
        st.session_state.day_count = 1
        st.session_state.show_index = 0
        st.session_state.last_night_info = ""
        st.session_state.last_execution = None
        st.session_state.win_side = None
        st.session_state.phase = "show_roles"
        st.experimental_rerun()

# =======================
# フェーズ: 役職確認
# =======================
elif st.session_state.phase == "show_roles":
    st.header("自分の役職確認フェーズ")

    idx = st.session_state.show_index
    n = st.session_state.num_players

    st.write("※端末をプレイヤーごとに渡して使ってください。")
    st.write(f"プレイヤー {idx+1} の番です。")

    if "show_role_flag" not in st.session_state:
        st.session_state.show_role_flag = False

    if st.button("役職を見る"):
        st.session_state.show_role_flag = True

    if st.session_state.show_role_flag:
        st.info(f"あなたの役職：{st.session_state.roles[idx]}")

    if st.button("画面を他の人に渡す（次へ）"):
        st.session_state.show_role_flag = False
        st.session_state.show_index += 1
        if st.session_state.show_index >= n:
            st.session_state.show_index = 0
            st.session_state.phase = "night"
            st.session_state.night_step = "wolf"
        st.experimental_rerun()

# =======================
# フェーズ: 夜
# =======================
elif st.session_state.phase == "night":
    st.header(f"{st.session_state.day_count} 日目の夜")

    st.write("※端末を各役職のプレイヤーにだけ渡して操作してください。")
    st.write("（他の人は画面を見ないようにしてください）")

    alive_players = get_alive_players()
    n = st.session_state.num_players
    roles = st.session_state.roles

    # 役職を持つプレイヤーのインデックス取得
    wolves = [i for i in alive_players if roles[i] == "人狼"]
    seers = [i for i in alive_players if roles[i] == "占い師"]
    guards = [i for i in alive_players if roles[i] == "騎士"]

    step = st.session_state.night_step

    # ---- 人狼ターン ----
    if step == "wolf":
        st.subheader("人狼のターン")

        if not wolves:
            st.write("生存している人狼はいません。")
            if st.button("次（占い師のターンへ）"):
                st.session_state.night_step = "seer"
                st.experimental_rerun()
        else:
            st.write("人狼のプレイヤーは協力して、襲撃する相手を1人決めてください。")
            target = st.selectbox(
                "襲撃するプレイヤーを選択",
                [i for i in alive_players if roles[i] != "人狼"],
                format_func=lambda x: f"プレイヤー {x+1}",
                key="wolf_target_select",
            )
            if st.button("このプレイヤーを襲撃する"):
                st.session_state.night_actions["wolf_target"] = target
                st.session_state.night_step = "seer"
                st.experimental_rerun()

    # ---- 占い師ターン ----
    elif step == "seer":
        st.subheader("占い師のターン")

        if not seers:
            st.write("生存している占い師はいません。")
            if st.button("次（騎士のターンへ）"):
                st.session_state.night_step = "guard"
                st.experimental_rerun()
        else:
            st.write("占い師は、占いたい相手を1人選びます。")
            target = st.selectbox(
                "占うプレイヤーを選択",
                [i for i in alive_players if i not in seers],
                format_func=lambda x: f"プレイヤー {x+1}",
                key="seer_target_select",
            )
            if st.button("このプレイヤーを占う"):
                st.session_state.night_actions["seer_target"] = target
                # 結果を占い師だけが見る前提だが、
                # 実際には口頭で伝える運用など、卓のルールに合わせてください。
                result_role = st.session_state.roles[target]
                is_wolf = (result_role == "人狼")
                st.success(
                    f"占い結果：プレイヤー {target+1} は "
                    + ("人狼です。" if is_wolf else "人狼ではありません。")
                )
                if st.button("占い師のターンを終了して次へ"):
                    st.session_state.night_step = "guard"
                    st.experimental_rerun()

    # ---- 騎士ターン ----
    elif step == "guard":
        st.subheader("騎士のターン")

        if not guards:
            st.write("生存している騎士はいません。")
            if st.button("次（夜の結果へ）"):
                st.session_state.night_step = "resolve"
                st.experimental_rerun()
        else:
            st.write("騎士は、守る相手を1人選びます。（自分を守れるかどうかは卓ルールで決めてください）")
            target = st.selectbox(
                "守るプレイヤーを選択",
                alive_players,
                format_func=lambda x: f"プレイヤー {x+1}",
                key="guard_target_select",
            )
            if st.button("このプレイヤーを守る"):
                st.session_state.night_actions["guard_target"] = target
                st.session_state.night_step = "resolve"
                st.experimental_rerun()

    # ---- 夜の結果処理 ----
    elif step == "resolve":
        st.subheader("夜の結果")

        wolf_target = st.session_state.night_actions["wolf_target"]
        guard_target = st.session_state.night_actions["guard_target"]

        killed = None
        info = ""

        if wolf_target is None:
            info = "昨夜は人狼の襲撃はありませんでした。"
        else:
            if guard_target is not None and wolf_target == guard_target:
                info = (
                    f"昨夜の死者はいません。"
                )
            else:
                # 襲撃成功
                if st.session_state.alive[wolf_target]:
                    st.session_state.alive[wolf_target] = False
                    killed = wolf_target
                    info = f"昨夜、プレイヤー {wolf_target+1} が無残な姿で発見されました。"
                else:
                    info = "昨夜は不思議なことに誰も死にませんでした。"

        st.session_state.last_night_info = info
        st.session_state.night_actions = {
            "wolf_target": None,
            "seer_target": None,
            "guard_target": None,
        }
        st.session_state.night_step = "wolf"

        st.write(info)

        # 勝敗チェック
        win = check_win()
        if win is not None:
            st.session_state.win_side = win
            st.session_state.phase = "result"
        else:
            st.session_state.phase = "day_talk"
        if st.button("朝になる"):
            st.experimental_rerun()

# =======================
# フェーズ: 昼（議論）
# =======================
elif st.session_state.phase == "day_talk":
    st.header(f"{st.session_state.day_count} 日目の昼")

    if st.session_state.last_night_info:
        st.info(st.session_state.last_night_info)

    st.write("ここからは口頭で議論を行ってください。")
    st.write("議論が終わったら「投票へ進む」を押してください。")

    alive_players = get_alive_players()
    st.write("現在生きているプレイヤー:")
    st.write(", ".join([f"{i+1}" for i in alive_players]))

    if st.button("投票へ進む"):
        st.session_state.votes = [None] * st.session_state.num_players
        st.session_state.vote_index = 0
        st.session_state.phase = "vote"
        st.experimental_rerun()

# =======================
# フェーズ: 投票
# =======================
elif st.session_state.phase == "vote":
    st.header(f"{st.session_state.day_count} 日目の投票")

    alive_players = get_alive_players()
    idx = st.session_state.vote_index

    if idx >= st.session_state.num_players:
        # 全員の投票が終わったら集計
        vote_count = {}
        for voter, target in enumerate(st.session_state.votes):
            if target is None:
                continue
            if target not in vote_count:
                vote_count[target] = 0
            vote_count[target] += 1

        if not vote_count:
            st.write("誰にも票が入りませんでした。処刑は行われません。")
            executed = None
        else:
            # 最多得票者
            max_votes = max(vote_count.values())
            candidates = [p for p, c in vote_count.items() if c == max_votes]
            if len(candidates) > 1:
                st.write("最多得票が複数人のため、ランダムで処刑します。")
                executed = random.choice(candidates)
            else:
                executed = candidates[0]

        st.session_state.last_execution = executed

        if executed is not None and st.session_state.alive[executed]:
            st.session_state.alive[executed] = False
            st.success(f"プレイヤー {executed+1} が処刑されました。")
        else:
            st.info("この日は誰も処刑されませんでした。")

        # 勝敗チェック
        win = check_win()
        if win is not None:
            st.session_state.win_side = win
            st.session_state.phase = "result"
        else:
            st.session_state.day_count += 1
            st.session_state.phase = "night"

        if st.button("次へ"):
            st.experimental_rerun()

    else:
        # 投票中
        if not st.session_state.alive[idx]:
            st.write(f"プレイヤー {idx+1} は死亡しているため投票できません。")
            if st.button("次のプレイヤーへ"):
                st.session_state.vote_index += 1
                st.experimental_rerun()
        else:
            st.write("※端末をプレイヤーごとに渡して使ってください。")
            st.subheader(f"プレイヤー {idx+1} の投票")

            target = st.selectbox(
                "投票する相手を選んでください",
                [p for p in alive_players if p != idx],
                format_func=lambda x: f"プレイヤー {x+1}",
                key=f"vote_target_{idx}",
            )

            if st.button("このプレイヤーに投票する"):
                st.session_state.votes[idx] = target
                st.session_state.vote_index += 1
                st.experimental_rerun()

# =======================
# フェーズ: 結果表示
# =======================
elif st.session_state.phase == "result":
    st.header("ゲーム終了")

    if st.session_state.win_side == "villager":
        st.success("村人陣営の勝利！")
    elif st.session_state.win_side == "wolf":
        st.error("人狼陣営の勝利！")
    else:
        st.info("引き分けまたは特殊な終了条件です。")

    st.subheader("最終状態")
    lines = []
    for i, role in enumerate(st.session_state.roles):
        status = "生存" if st.session_state.alive[i] else "死亡"
        lines.append(f"プレイヤー {i+1}: {role} / {status}")
    st.write("\n".join(lines))

    if st.button("もう一度遊ぶ"):
        init_game_state()
        st.experimental_rerun()
