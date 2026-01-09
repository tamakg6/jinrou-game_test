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
    st.session_state.night_player_index = 0
    st.session_state.seer_done_today = False
    st.session_state.last_seer_result = None


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
        st.rerun()

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
        st.session_state.seer_done_today = False  # この夜に占い師が占い済みか
        st.rerun()

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
        st.rerun()
# =======================
# フェーズ: 夜（プレイヤー順に回す版）
# =======================
elif st.session_state.phase == "night":
    st.header(f"{st.session_state.day_count} 日目の夜")
    
    st.write("※プレイヤー1→2→3…の順に端末を回してください。")
    st.write("自分の番になったら、自分の行動を入力して「次へ」を押してください。")
    
    alive_players = get_alive_players()
    
    if "night_player_index" not in st.session_state:
        st.session_state.night_player_index = 0
        st.session_state.seer_done_today = False
        st.session_state.last_seer_result = None
    
    current_player = st.session_state.night_player_index
    n = st.session_state.num_players
    roles = st.session_state.roles
    
    # 全員の行動が終わったかチェック
    if current_player >= len(alive_players):
        st.subheader("夜の行動が終了しました")
        
        # 夜の結果処理
        wolf_target = st.session_state.night_actions["wolf_target"]
        guard_target = st.session_state.night_actions["guard_target"]
        
        if wolf_target is None:
            st.session_state.last_night_info = "昨夜は人狼の襲撃はありませんでした。"
        else:
            if guard_target is not None and wolf_target == guard_target:
                st.session_state.last_night_info = (
                    f"昨夜、人狼はプレイヤー {wolf_target+1} を襲撃しましたが、"
                    "騎士の護衛により守られました。"
                )
            else:
                if st.session_state.alive[wolf_target]:
                    st.session_state.alive[wolf_target] = False
                    st.session_state.last_night_info = f"昨夜、プレイヤー {wolf_target+1} が無残な姿で発見されました。"
                else:
                    st.session_state.last_night_info = "昨夜は不思議なことに誰も死にませんでした。"
        
        st.write(st.session_state.last_night_info)
        
        # 勝敗チェック
        win = check_win()
        if win is not None:
            st.session_state.win_side = win
            st.session_state.phase = "result"
        else:
            st.session_state.phase = "day_talk"
            
        if st.button("朝になる"):
            st.session_state.night_actions = {
                "wolf_target": None,
                "seer_target": None,
                "guard_target": None,
            }
            st.session_state.seer_done_today = False
            st.session_state.night_player_index = 0
            st.session_state.day_count += 1
            st.rerun()
        return
    
    # 現在のプレイヤーの行動フェーズ
    st.subheader(f"プレイヤー {current_player+1} の番")
    st.info(f"あなたの役職：{roles[current_player]}")
    
    if not st.session_state.alive[current_player]:
        st.write("死亡しているため行動はありません。")
        if st.button("次へ"):
            st.session_state.night_player_index += 1
            st.rerun()
        return
    
    # 役職ごとの行動
    if roles[current_player] == "人狼":
        st.write("人狼は襲撃対象を選びます。（複数人狼の場合は相談して1人決めてください）")
        targets = [i for i in get_alive_players() if roles[i] != "人狼"]
        if targets and st.session_state.night_actions["wolf_target"] is None:
            target = st.selectbox(
                "襲撃対象を選んでください",
                targets,
                format_func=lambda x: f"プレイヤー {x+1}",
                key=f"wolf_select_{current_player}",
            )
            if st.button("襲撃を決定"):
                st.session_state.night_actions["wolf_target"] = target
                st.success(f"プレイヤー {target+1} を襲撃対象に決定しました。")
                st.rerun()
        else:
            st.write("人狼の襲撃は決定済みです。")
    
    elif roles[current_player] == "占い師":
        if st.session_state.seer_done_today:
            st.write("今夜はすでに占いを完了しています。")
        else:
            st.write("占い師は1晩に1人だけ占えます。")
            targets = [i for i in get_alive_players() if i != current_player]
            target = st.selectbox(
                "占う相手を選んでください",
                targets,
                format_func=lambda x: f"プレイヤー {x+1}",
                key=f"seer_select_{current_player}",
            )
            if st.button("占う", key=f"occupy_{current_player}"):
                result_role = roles[target]
                is_wolf = (result_role == "人狼")
                st.session_state.night_actions["seer_target"] = target
                st.session_state.seer_done_today = True
                st.session_state.last_seer_result = {
                    "target": target,
                    "is_wolf": is_wolf
                }
                st.rerun()
        
        # 占い結果表示
        if "last_seer_result" in st.session_state and st.session_state.last_seer_result:
            res = st.session_state.last_seer_result
            result_text = f"占い結果：プレイヤー {res['target']+1} は " + \
                         ("**人狼** です！" if res['is_wolf'] else "**村人陣営** です。")
            st.markdown(f"### {result_text}")
    
    elif roles[current_player] == "騎士":
        st.write("騎士は護衛対象を選びます。")
        targets = get_alive_players()
        if targets and st.session_state.night_actions["guard_target"] is None:
            target = st.selectbox(
                "守る相手を選んでください",
                targets,
                format_func=lambda x: f"プレイヤー {x+1}",
                key=f"guard_select_{current_player}",
            )
            if st.button("護衛を決定"):
                st.session_state.night_actions["guard_target"] = target
                st.success(f"プレイヤー {target+1} を護衛対象に決定しました。")
                st.rerun()
        else:
            st.write("騎士の護衛は決定済みです。")
    
    else:  # 村人、霊媒師など
        st.write("あなたの役職に夜の行動はありません。")
    
    # 次へ進むボタン
    if st.button("次へ"):
        st.session_state.night_player_index += 1
        st.rerun()


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
        st.rerun()

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
            st.rerun()

    else:
        # 投票中
        if not st.session_state.alive[idx]:
            st.write(f"プレイヤー {idx+1} は死亡しているため投票できません。")
            if st.button("次のプレイヤーへ"):
                st.session_state.vote_index += 1
                st.rerun()
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
                st.rerun()

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
        st.rerun()
