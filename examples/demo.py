import os
import sys
from datetime import datetime
from pathlib import Path

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

CHAT_LOG_FAILED_DEESCALATION = """[16:20:00] TechBro: python is literally a toy language, use rust or go home
[16:20:12] PyDev: okay enjoy writing 300 lines for what takes me 10 in python
[16:20:25] TechBro: speed matters, python devs just dont get it
[16:20:40] PyDev: speed matters for like 2% of use cases, cope
[16:20:55] TechBro: this is why python devs never get senior roles lmao
[16:21:10] PyDev: bro ur literally a junior with a blog post, relax
[16:21:20] CodeNewbie: guys they're both good languages for different things haha
[16:21:28] TechBro: nobody asked for ur beginner take
[16:21:35] PyDev: seriously stay out of it
[16:21:40] CodeNewbie: okay sorry 😅
[16:21:50] TechBro: python devs always travel in packs to defend their garbage language
[16:22:05] PyDev: ur genuinely one of the most insufferable people ive talked to online
[16:22:10] ** CodeNewbie left the room **
[16:22:18] ** RandomLurker left the room **"""

CHAT_LOG_SELF_RESOLVING = """[19:00:00] MusicFan1: lofi is the most boring genre to ever exist
[19:00:12] LofiLover: its literally for studying/relaxing, thats the point??
[19:00:25] MusicFan1: why would u listen to music that puts u to sleep
[19:00:38] LofiLover: why would u come into a lofi room to complain lmao
[19:00:50] MusicFan1: fair point actually 💀
[19:01:05] LofiLover: lol just let people enjoy things man
[19:01:20] MusicFan1: yeah ur right my bad, got off work and im just in a mood
[19:01:35] LofiLover: lmaooo okay fair, hope ur night gets better
[19:01:50] MusicFan1: 😂 thanks bro. whats this song playing rn its actually not bad"""

CHAT_LOG_MULTI_PARTY = """[20:10:00] User_Alpha: this movie was mid at best
[20:10:08] CinemaFan: are you serious it was a masterpiece
[20:10:15] User_Alpha: masterpiece 💀 the ending made no sense
[20:10:22] FilmBuff: the ending was literally the whole point, did u even watch it
[20:10:30] User_Alpha: i watched it, it was pretentious garbage
[20:10:38] CinemaFan: ur just not smart enough to get it, simple
[20:10:45] User_Alpha: oh so now i have to be smart to enjoy a movie lmaooo
[20:10:52] FilmBuff: clearly some people watch films and some people just consume content
[20:11:00] User_Beta: can yall chill im trying to listen to the playlist
[20:11:08] CinemaFan: then mute the chat??
[20:11:15] User_Beta: why should i mute, ur the ones arguing
[20:11:22] FilmBuff: nobody told u to read it
[20:11:30] User_Alpha: this whole room is actually insufferable
[20:11:35] ** User_Beta left the room **
[20:11:40] ** SilentOne left the room **
[20:11:42] ** AnotherOne left the room **"""


def main():

    # Select which chat log to test with by changing the variable below. Each log is designed to test different aspects of the mediator's functionality.
    chat = CHAT_LOG_MULTI_PARTY

    # LLM configuration - set your LLM API key and model here.
    LLM_config = {
        "api_key": os.getenv("GROQ_API_KEY"),
        "model": "llama-3.1-8b-instant",
        "base_url": "https://api.groq.com"
    }

    room_config = {
        "room_name": "Chill Vibes",
        "region": "Indonesian",
        "admin_username": "RoomBoss",
        "admin_last_active": datetime(2026, 5, 14, 14, 2, 0),
        "confidence_threshold": 80.0,
    }


    print(f"API key found: {LLM_config['api_key'] is not None}")
    if not LLM_config["api_key"]:
        print("Error: GROQ_API_KEY not set in environment")
        print("Set it with: $env:GROQ_API_KEY='your-key'")
        print("You can get a free key from https://groq.com")
        return

    print(f"Using API key: {LLM_config['api_key'][:20]}...")

    print("=" * 60)
    print("AI Conflict Mediator Demo")
    print(f"Room: {room_config['room_name']} | Region: {room_config['region']}")
    print("Mode: LLM-based")
    print("=" * 60)
    print()

    mediator = create_mediator(   
        api_key=LLM_config["api_key"],
        model=LLM_config["model"],
        base_url=LLM_config["base_url"],
        **room_config
    )

    print(f"Initial Status: {mediator.get_status()}")
    print()

    messages = [line.strip() for line in chat.strip().split("\n")]

    for i, msg in enumerate(messages, 1):
        safe_msg = msg.encode('ascii', 'replace').decode('ascii')[:60]
        print(f"[{i}] Processing: {safe_msg}...")

        result = mediator.process_message(msg)

        if result:
            print(f"    -> INTERVENTION TRIGGERED")
            if result.admin_alert:
                print(f"    -> Severity: {result.admin_alert.severity}")
            elif result.chat_message:
                print(f"    -> Severity: [from chat message context]")

            if result.chat_message:
                print(f"    -> AI Says: \"{result.chat_message}\"")
            else:
                print(f"    -> No chat message (AI was attacked)")

            if result.admin_alert:
                print(f"    -> Admin Alert: {result.admin_alert}")

        print()

    print("=" * 60)
    print("Final Status:")
    print(mediator.get_status())
    print("=" * 60)


if __name__ == "__main__":
    main()