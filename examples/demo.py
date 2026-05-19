import os
import sys
from datetime import datetime
from pathlib import Path

import dotenv

dotenv.load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chatmoderation import create_mediator


CHAT_LOG = """[14:05:00] DramaKing: bro that drama was trash, how can anyone like it 😂
[14:05:08] K-DramaFan: excuse me?? it won best drama award, ur taste is just bad lol
[14:05:22] DramaKing: awards dont mean anything, ppl who like that show have zero taste fr
[14:05:30] SilentViewer: 😬😬😬
[14:05:45] K-DramaFan: lmao says the guy whose profile pic is from a 2015 anime, go back to ur basement
[14:06:02] DramaKing: at least im not some braindead fan who worships everything korea makes, typical
[14:06:10] PeaceLover: guys chill its just a show...
[14:06:25] K-DramaFan: shut up nobody asked u. and @DramaKing ur literally the dumbest person in this room rn
[14:06:28] ** NewUser_823 left the room **
[14:06:35] ** JustHere4Fun left the room **"""

CHAT_LOG_SLOW_BURN = """[14:00:00] FootballFan99: bro ronaldo is so overrated its not even funny
[14:00:45] CR7Forever: lol okay casual fan detected
[14:01:30] FootballFan99: im just saying messi does everything better, stats dont lie
[14:02:10] CR7Forever: messi fans are so insufferable fr
[14:02:55] FootballFan99: at least i actually watch the sport
[14:03:40] CR7Forever: says the guy who probably started watching in 2018 lmao
[14:04:15] FootballFan99: bro what is ur problem, i was just talking about football
[14:04:20] LurkMode: 👀
[14:04:50] CR7Forever: ur problem is u dont know what ur talking about, simple
[14:05:10] FootballFan99: okay ur actually so toxic why are you like this
[14:05:30] CR7Forever: cry about it
[14:05:45] ** LurkMode left the room **"""

CHAT_LOG_BANTER = """[15:10:00] GamerBro: ngl ur aim in that clip was actually criminal 💀
[15:10:08] ProGamer99: i was lagging bro dont even
[15:10:15] GamerBro: lagging lmaooo sure sure
[15:10:22] ProGamer99: ill 1v1 u rn and we'll see whos lagging
[15:10:30] GamerBro: dont make promises u cant keep 😭
[15:10:45] ProGamer99: ur so cooked when i get home
[15:10:52] GamerBro: talk is cheap send the invite
[15:11:00] ProGamer99: ur going to cry and i will record it
[15:11:10] GamerBro: LMAOO okay big talk
[15:11:20] CasualViewer: 😂😂 this room is so funny
[15:11:35] ProGamer99: he always does this btw, all talk no game"""
CHAT_LOG_BANTER = """[15:10:00] GamerBro: ngl ur aim in that clip was actually criminal 💀
[15:10:08] ProGamer99: i was lagging bro dont even
[15:10:15] GamerBro: lagging lmaooo sure sure
[15:10:22] ProGamer99: ill 1v1 u rn and we'll see whos lagging
[15:10:30] GamerBro: dont make promises u cant keep 😭
[15:10:45] ProGamer99: ur so cooked when i get home
[15:10:52] GamerBro: talk is cheap send the invite
[15:11:00] ProGamer99: ur going to cry and i will record it
[15:11:10] GamerBro: LMAOO okay big talk
[15:11:20] CasualViewer: 😂😂 this room is so funny
[15:11:35] ProGamer99: he always does this btw, all talk no game"""

def main():
    api_key = os.getenv("OPENROUTER_API_KEY")
    print(api_key)
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set in environment")
        print("Set it with: $env:OPENROUTER_API_KEY='your-key'")
        print("You can get a free key from https://openrouter.ai")
        return

    print(f"Using API key: {api_key[:20]}...")

    print("=" * 60)
    print("AI Conflict Mediator Demo")
    print("Room: Chill Vibes | Region: Indonesian")
    print("Mode: LLM-based")
    print("=" * 60)
    print()

    mediator = create_mediator(   
        api_key=api_key,
        model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
        room_name="Chill Vibes",
        region="Indonesian",
        admin_username="RoomBoss",
        admin_last_active=datetime(2026, 5, 14, 14, 2, 0),
        confidence_threshold=80.0,
    )

    print(f"Initial Status: {mediator.get_status()}")
    print()

    messages = [line.strip() for line in CHAT_LOG.strip().split("\n")]

    for i, msg in enumerate(messages, 1):
        safe_msg = msg.encode('ascii', 'replace').decode('ascii')[:60]
        print(f"[{i}] Processing: {safe_msg}...")

        result = mediator.process_message(msg)

        if result:
            print(f"    -> INTERVENTION TRIGGERED")
            print(f"    -> Severity: {result.severity.value}")

            if result.chat_message:
                print(f"    -> AI Says: \"{result.chat_message}\"")
            else:
                print(f"    -> No chat message (AI was attacked)")

            if result.admin_alert:
                print(f"    -> Admin Alert: {result.admin_alert[:80]}...")

        print()

    print("=" * 60)
    print("Final Status:")
    print(mediator.get_status())
    print("=" * 60)


if __name__ == "__main__":
    main()