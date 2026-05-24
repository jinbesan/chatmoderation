# Initial prompt:

AI Conflict Mediator

A voice chat room called “Chill Vibes” is anything but chill right now. What started as a TV show debate has turned into personal attacks. Two bystanders already left. The room admin hasn’t touched anything in 4 minutes. Someone tried to play peacemaker and immediately got told to shut up.

Your job: build an AI that watches the chat, decides if things have gone too far, and says something to cool it down — without sounding like a robot or making it worse.

For context: about 8% of voice chat rooms see at least one conflict per day. On average, it takes a human admin 45 seconds to even notice.

Build this

An AI that takes a chat stream and outputs: 

1. Should it intervene? (yes/no) 

2. How bad is it? (low / medium / high) 

3. What does it say?



```

Chat log

Room: “Chill Vibes 🎵”, Indonesian region, 10 users online. Admin “RoomBoss” last active at 14:02.

[14:05:00] DramaKing: bro that drama was trash, how can anyone like it 😂
[14:05:08] K-DramaFan: excuse me?? it won best drama award, ur taste is just bad lol
[14:05:22] DramaKing: awards dont mean anything, ppl who like that show have zero taste fr
[14:05:30] SilentViewer: 😬😬😬
[14:05:45] K-DramaFan: lmao says the guy whose profile pic is from a 2015 anime, go back to ur basement
[14:06:02] DramaKing: at least im not some braindead fan who worships everything korea makes, typical
[14:06:10] PeaceLover: guys chill its just a show...
[14:06:25] K-DramaFan: shut up nobody asked u. and @DramaKing ur literally the dumbest person in this room rn
[14:06:28] ** NewUser_823 left the room **
[14:06:35] ** JustHere4Fun left the room **
```


Think about

Where’s the line? m001 is banter. m008 is hostile. Somewhere in between, it crossed over. What signals does your AI use — just the words, or also things like 😬😬😬, the failed peacemaker, and people leaving?

Different levels need different responses. A joke to change the subject at m003 is very different from an intervention at m008. Show at least two tiers.

What if the AI gets attacked too? PeaceLover tried and got shut down. What’s Plan B if the same happens to your AI?

Plan:
I want to build a 2 agent system.
Agent 1: conflict classifier
- Takes in the chat status (context: online users, admin presence, people joining/leaving, time between last messages) chat stream (rolling window of size N, configurable, default N=10), assign conflict severity of each message.
- Input is JSON structured input: 1. chat context block with precomputed signals, 2. chat rolling window with Agent 1's past severity tags appended.
- Look out for contextual signals, not just word choices but also how fast the chat is moving, topic change (conflict moving from attacks on show to attacks on person), if people are leaving the room and failed de escalation.
- Track pronoun shift (indicator that conflict is getting personal)
- Monitor reciprocity of comments, if both ends are mutually playful it can be considered banter, if only one end is receiving, it is more hostile.
- A list of blacklisted words such as slurs will be given. Blacklisted words are not the only criterion, but can cause a hard override of the classification, can bump the severity up straight to High
Agent 1 will only output the severity level (None/Low/Medium/High), confidence level of the classification (0-100%) and whether to intervene or not, to tag the last message of the rolling window.
The severity level tags outputted by Agent 1 will subsequently be appended to the window by the system in between calls to each message, to be used for input in Agent 1's subsequent calls.


Agent 2 is the intervention writer
- Takes in the same context as Agent 1 (rolling window and chat context), and also the output of Agent 1, and creates a response in the chat.
- Region/language/culture/topic is relevant when creating a response, so this agent should take those into account and match the register. Use what the room has said so far as a style guide on what to say
- Agent 2 should have different behavioural modes when writing intervention, based on the severity of conflict, different levels should be treated differently when trying to intervene. For example: Low: subtle topic redirect, Medium: acknowledge tension+topic redirect, High: be more direct but not preachy
- Lower severity levels should allow users to have an easy exit out of the conflict to save face, and reinvite participation while closing the conflict discussion, without making anyone feel called out
- At High severity, Agent 2 should also separately inform the moderator privately, with a summarization of the conflict and the timestamp.
If the AI has already intervened and received a hostile response (tracked in state), Agent 2 should not generate a chat message. Instead it should only generate an admin alert.
The admin alert should be a short structured message containing: severity level, timestamp of escalation, a short summary of what happened, number of users who left, and whether the AI already intervened.

Non Agent system: State tracker (part of chat state to be passed into Agent 1 and Agent 2)
- tracks current severity trend (stable, escalating, deescalating)
- If AI has already intervened
- Admin availability
- Number of users who have left
This information will be useful for Agent 1 in deciding severity labels, and in determining what action to take next based on Agent 1's output.
Agent 2 is only called if intervention_needed is true AND confidence ≥ X%. Below that threshold, only an admin alert is sent if severity is Medium or above.


# Fixing Prompts

### 1
Comments on the output:
State should be updated after each recent message processed. This way, the AI will not send similar messages repeatedly as seen from messages 7 onward. 
Intervention prompt should also be adjusted: Do not hardcode region, and rewrite the prompt such that it will sound more natural, and not always generate similar sounding texts like "(suggestions to chill) - anyone want to change the subject?" 
This will instantly make the chatters realize this is a bot and will attack the bot: this is not ideal.
Admin alerts are too frequent and the summaries are unclear and generic. 

Message 8: Severity detected as None: there is an issue here, find out what makes the classifier classify it as None and fix it.

Create a plan for what needs to be fixed, ask the necessary questions and I will confirm the changes to be sent to the build agent.

### 2
Fix 1: After agent 2 decides what to do, the state should also be updated with if Agent 2 has intervened. This way, Agent 2 will not intervene repeatedly in short intervals.
Agent 2 should only intervene a few times every conflict cycle (severity trend increase -> decrease -> none)

Next, I have added a list of words in words.json. for the blacklist. 
Update the blacklist to load this file.
Because this file is very long, do not load these words into the prompt. Instead, search the message if it contains any of these words, and include into the prompt that it contains X blacklisted words, and to take that into consideration when evaluating severity score. It does not need to automatically bump the severity to High, but the presence of blacklisted words will add to the severity score.

### 3
Slight change: current observation is that the mediator intervenes at Medium severity, and doesn't intervene anymore since it's still on cooldown. Make it such that it's able to intervene again only once it reaches High, and refreshes the cooldown, and is no longer able to intervene (even if the next message is at High), until the cooldown is over.

### 4
I noticed a problem with the admin alert system.

In line 107:
if not agent2_output.chat_message and agent1_output.severity >= SeverityLevel.MEDIUM:
and line 116:
if agent1_output.severity >= SeverityLevel.MEDIUM and agent1_output.confidence >= self.confidence_threshold:

there is comparisons with the SeverityLevel enum.
However, SeverityLevel.NONE = "None" and SeverityLevel.MEDIUM = "Medium", which causes a string comparison. Since "None" > "Medium" is true, an admin alert is sent out which is incorrect behaviour. Similarly. SeverityLevel.HIGH > SeverityLevel.MEDIUM is false, which also results in incorrect behaviour. 

We can correct this behaviour by making the value of the SeverityLevel enum a (str,int) tuple, where SeverityLevel.NONE = ("None", 0), etc, and overriding __new__() to support a multiple attribute enum.


# Creating Tests

```python
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


```

help me write more sample chatlogs like this for me to test.

# User files
Create an .md file with the history of my commands to you.
Create a README.md on how to use the package, and how to use demo.py

# Refining System Prompts
### 1
Please help to evaluate the current system prompt for agent 2. I feel that currently, the responses are too robotic and awkward in context: It always says something like, "woah, It's getting out of hand - anyway anyone catch (thing)?"

Please help to improve this prompt and help to make it sound more natural.
### 2
Help me refine the Agent 1 prompt as well
### 3
Regarding the Agent 1 system prompt:

Compound signals: pronoun shift + departures + failed peacemaker all present
pronouun shift and failed peacemaker is quite ambiguous, and agent 1 keeps labelling these signals when there really isn't anything there. Help me to edit Agent 1 system prompt again.