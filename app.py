import random
import os
import sys
from typing import List, Optional
from dataclasses import dataclass


def clear_screen():
    """画面をクリア（Windows/Linux/Mac対応）"""
    if os.name == "nt":  # Windows
        os.system("cls")
    else:  # Mac/Linux
        os.system("clear")


@dataclass
class Player:
    """プレイヤークラス"""
    name: str
    role: str  # "villager", "werewolf", "seer", "hunter", "madman"
    alive: bool = True


class WerewolfGame:
    """人狼ゲームメインクラス"""
    
    # 役職の日本語名
    ROLES_JP = {
        "villager": "村人",
        "werewolf": "人狼", 
        "seer": "占い師",
        "hunter": "狩人",
        "madman": "狂人"
    }
    
    # 勝利陣営
    WIN_VILLAGE = "村陣営"
    WIN_WEREWOLF = "人狼陣営"
    
    def __init__(self):
        self.players: List[Player] = []
        self.day = 1
        self.is_night = True
        self.game_log: List[str] = []
        self.night_victim: Optional[Player] = None
        self.protected_player: Optional[Player] = None
        
    def run_game(self):
        """ゲーム全体の実行"""
        try:
            self.setup_game()
            self.game_loop()
        except KeyboardInterrupt:
            print("\n\n=== ゲーム中断 ===")
            sys.exit(0)
    
    def setup_game(self):
        """ゲーム初期化"""
        clear_screen()
        print("🎭=== テキスト人狼ゲーム (1端末回しプレイ) ===🎭")
        print("プレイ人数: 4〜8人 / 役職: 村人・人狼・占い師・狩人・狂人\n")
        
        # 人数入力
        player_count = self._input_player_count()
        
        # 名前入力
        player_names = self._input_player_names(player_count)
        
        # 役職決定
        roles = self._generate_roles(player_count)
        random.shuffle(roles)
        
        # プレイヤー作成
        self.players = [Player(name, role) for name, role in zip(player_names, roles)]
        
        # 役職シークレット確認
        self._show_roles_secretly()
        
    def _input_player_count(self) -> int:
        """プレイヤー人数入力"""
        while True:
            try:
                count = int(input("📊 プレイヤー人数 (4-8): "))
                if 4 <= count <= 8:
                    return count
                print("❌ 4〜8人の範囲で入力してください")
            except ValueError:
                print("❌ 数値を入力してください")
    
    def _input_player_names(self, count: int) -> List[str]:
        """プレイヤー名前入力"""
        names = []
        for i in range(1, count + 1):
            while True:
                name = input(f"👤 プレイヤー{i}の名前: ").strip()
                if name:
                    names.append(name)
                    break
                print("❌ 空の名前は不可です")
        return names
    
    def _generate_roles(self, count: int) -> List[str]:
        """役職自動配分"""
        role_distributions = {
            4: ["werewolf", "seer", "villager", "villager"],
            5: ["werewolf", "seer", "madman", "villager", "villager"],
            6: ["werewolf", "werewolf", "seer", "hunter", "villager", "villager"],
            7: ["werewolf", "werewolf", "seer", "hunter", "madman", "villager", "villager"],
            8: ["werewolf", "werewolf", "seer", "hunter", "madman", "villager", "villager", "villager"]
        }
        return role_distributions.get(count, ["werewolf", "seer"] + ["villager"] * (count - 2))
    
    def _show_roles_secretly(self):
        """役職を1人ずつ秘密裏に表示"""
        clear_screen()
        print("🔒=== 役職確認タイム（重要！） ===")
        print("📱 端末を順番に回して各自の役職を確認してください\n")
        
        for player in self.players:
            print(f"\n🎯 {player.name} さんの番です")
            input("👀 準備ができたら Enter を押してください...")
            
            clear_screen()
            print(f"🎭 {player.name} さんの役職")
            print("=" * 40)
            print(f"  🎭 {self.ROLES_JP[player.role]} 🎭")
            print("=" * 40)
            print("\n⚠️  絶対に他の人に見せないでください！")
            input("✅ 確認後、Enter で次へ...")
            clear_screen()
        
        print("🎉 全員の役職確認完了！")
        input("\n🚀 Enter で1日目の夜を開始...")
    
    def game_loop(self):
        """メインゲームループ"""
        while True:
            if self.is_night:
                self.night_phase()
                if self.check_victory():
                    break
                self.is_night = False
            else:
                self.day_phase()
                if self.check_victory():
                    break
                self.is_night = True
                self.day += 1
        
        self.show_final_result()
    
    def night_phase(self):
        """夜フェーズ"""
        self.night_victim = None
        self.protected_player = None
        
        clear_screen()
        print(f"🌙=== {self.day}日目の夜 ===")
        input("\n👀 全員目をつぶってください... Enter")
        
        # 人狼の襲撃
        self.werewolf_action()
        
        # 占い師の行動
        self.seer_action()
        
        # 狩人の護衛
        self.hunter_action()
        
        # 夜結果確定
        self.resolve_night_result()
        
        # 朝の発表
        clear_screen()
        print(f"🌅=== {self.day}日目の朝 ===")
        if self.night_victim:
            print(f"💀 {self.night_victim.name} さんが襲撃されました...")
            self.game_log.append(f"夜{self.day}: {self.night_victim.name} 死亡")
        else:
            print("✨ 昨夜は平穏でした")
            self.game_log.append(f"夜{self.day}: 無事")
        input("\n📢 全員で状況確認後、Enter で昼フェーズへ...")
    
    def werewolf_action(self):
        """人狼の襲撃選択"""
        wolves = [p for p in self.players if p.role == "werewolf" and p.alive]
        if not wolves:
            return
        
        clear_screen()
        print("🐺=== 人狼タイム ===")
        wolf_names = " / ".join([w.name for w in wolves])
        input(f"\n{wolf_names} さんだけ画面を見てください... Enter")
        
        clear_screen()
        print("🎯 襲撃対象選択（自分以外）")
        targets = [p for p in self.players if p.alive and p.role != "werewolf"]
        for i, target in enumerate(targets, 1):
            print(f"{i:2d}. {target.name}")
        
        while True:
            choice = input("\n番号を入力（スキップ=Enter）: ").strip()
            if not choice:
                print("今夜は襲撃なし")
                input("Enter で終了...")
                break
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(targets):
                    self.night_victim = targets[idx]
                    print(f"✅ {self.night_victim.name} を襲撃決定")
                    input("Enter で人狼終了...")
                    break
                else:
                    print("❌ 番号が範囲外です")
            except ValueError:
                print("❌ 数値を入力してください")
        
        clear_screen()
        input("🐺 人狼は目を閉じてください... Enter")
    
    def seer_action(self):
        """占い師の占い"""
        seers = [p for p in self.players if p.role == "seer" and p.alive]
        if not seers:
            return
        
        seer = seers[0]  # 占い師1人想定
        
        clear_screen()
        print("🔮=== 占い師タイム ===")
        input(f"\n{seer.name} さんだけ画面を見てください... Enter")
        
        clear_screen()
        print("🎯 占い対象選択")
        targets = [p for p in self.players if p.alive and p != seer]
        for i, target in enumerate(targets, 1):
            print(f"{i:2d}. {target.name}")
        
        choice = input("\n番号を入力（スキップ=Enter）: ").strip()
        if choice:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(targets):
                    target = targets[idx]
                    result = "人狼陣営" if target.role in ["werewolf", "madman"] else "村陣営"
                    print(f"✅ {target.name}: {result}")
                    input("Enter で終了...")
            except ValueError:
                pass
        
        clear_screen()
        input("🔮 占い師は目を閉じてください... Enter")
    
    def hunter_action(self):
        """狩人の護衛"""
        hunters = [p for p in self.players if p.role == "hunter" and p.alive]
        if not hunters:
            return
        
        hunter = hunters[0]
        
        clear_screen()
        print("🛡️=== 狩人タイム ===")
        input(f"\n{hunter.name} さんだけ画面を見てください... Enter")
        
        clear_screen()
        print("🎯 護衛対象選択")
        targets = [p for p in self.players if p.alive]
        for i, target in enumerate(targets, 1):
            print(f"{i:2d}. {target.name}")
        
        choice = input("\n番号を入力（スキップ=Enter）: ").strip()
        if choice:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(targets):
                    self.protected_player = targets[idx]
                    print(f"✅ {self.protected_player.name} を護衛")
                    input("Enter で終了...")
            except ValueError:
                pass
        
        clear_screen()
        input("🛡️ 狩人は目を閉じてください... Enter")
    
    def resolve_night_result(self):
        """夜の結果確定"""
        if self.night_victim and self.night_victim != self.protected_player:
            self.night_victim.alive = False
    
    def day_phase(self):
        """昼フェーズ"""
        clear_screen()
        print(f"☀️=== {self.day}日目の昼 ===")
        print("\n👥 生存者一覧:")
        alive_players = [p for p in self.players if p.alive]
        for p in alive_players:
            print(f"  • {p.name}")
        
        print("\n💬 ここで議論を行ってください")
        input("🗳️  議論終了後、Enter で投票フェーズへ...")
        
        self.voting_phase()
    
    def voting_phase(self):
        """投票フェーズ"""
        alive_players = [p for p in self.players if p.alive]
        votes = {p.name: 0 for p in alive_players}
        
        clear_screen()
        print(f"🗳️=== {self.day}日目 投票タイム ===")
        
        for voter in alive_players:
            print(f"\n🎯 {voter.name} さんの投票")
            input(f"{voter.name} さんだけ画面を見てください... Enter")
            
            clear_screen()
            candidates = [p for p in alive_players if p != voter]
            print("投票先:")
            for i, cand in enumerate(candidates, 1):
                print(f"{i:2d}. {cand.name}")
            
            while True:
                choice = input("\n番号を入力（棄権=Enter）: ").strip()
                if not choice:
                    print("✅ 投票棄権")
                    input("Enter で次へ...")
                    break
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(candidates):
                        target = candidates[idx]
                        votes[target.name] += 1
                        print(f"✅ {target.name} に投票")
                        input("Enter で次へ...")
                        break
                except ValueError:
                    print("❌ 数値を入力")
        
        # 投票結果発表
        self.announce_voting_result(votes)
    
    def announce_voting_result(self, votes: dict):
        """投票結果発表と処刑"""
        clear_screen()
        print("📊=== 投票結果 ===")
        for name, count in sorted(votes.items(), key=lambda x: x[1], reverse=True):
            print(f"{name}: {count}票")
        
        max_votes = max(votes.values()) if votes else 0
        if max_votes == 0:
            print("\n🤝 投票棄権多数で処刑者なし")
            self.game_log.append(f"昼{self.day}: 処刑なし")
            input("Enter で次へ...")
            return
        
        # 最多票者確定
        candidates = [name for name, v in votes.items() if v == max_votes]
        executed_name = random.choice(candidates) if len(candidates) > 1 else candidates[0]
        
        executed = next(p for p in self.players if p.name == executed_name)
        executed.alive = False
        
        clear_screen()
        print("⚰️=== 処刑結果 ===")
        print(f"{executed.name} さんが処刑されました...")
        print(f"正体: 🎭 {self.ROLES_JP[executed.role]}")
        self.game_log.append(f"昼{self.day}: {executed.name}({self.ROLES_JP[executed.role]})処刑")
        input("Enter で次へ...")
    
    def check_victory(self) -> bool:
        """勝利条件チェック"""
        alive_players = [p for p in self.players if p.alive]
        alive_wolves = [p for p in alive_players if p.role == "werewolf"]
        alive_villagers = [p for p in alive_players if p.role != "werewolf"]
        
        if not alive_wolves:
            self.winner = self.WIN_VILLAGE
            return True
        if len(alive_wolves) >= len(alive_villagers):
            self.winner = self.WIN_WEREWOLF
            return True
        return False
    
    def show_final_result(self):
        """最終結果表示"""
        clear_screen()
        print("🏁=== ゲーム終了 ===")
        print(f"🎉 {self.winner} の勝利！")
        
        print("\n📋 全員の役職と結果")
        print("-" * 50)
        for player in self.players:
            status = "🟢生存" if player.alive else "🔴死亡"
            print(f"{player.name:10s} | {self.ROLES_JP[player.role]:8s} | {status}")
        
        print("\n📜 ゲームログ")
        print("-" * 50)
        for log in self.game_log:
            print(log)
        
        print("\n🎮 お疲れさまでした！")
        input("👋 Enter で終了...")


def main():
    """メイン実行関数"""
    game = WerewolfGame()
    game.run_game()


if __name__ == "__main__":
    main()
