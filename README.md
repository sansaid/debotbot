# Debotbot

The Telegram bot that's there to help you structure your debates with friends

## Usage

Add @debotbot_bot to your Telegram group and make sure it has *admin* privileges so that it may pin messages to the group (it's not sufficient to give it the ability to pin messages at this time).

## Commands

Commmands are split into two subtyypes: a *command* and a *tag*. Commands trigger actions from the bot, where as tags are decorative and do not trigger actions by the bot. They are used to label messages and you are encouraged to send only taggable message during a debate. Debotbot will use this information to send statistics about the debate after it has concluded.

* `/debate <proposition>` - Start a debate with a proposition. **Example:** `/debate Pies are better than cake`
* `/moderate` - Nominate yourself as a moderator. Can only be used after a debate has been proposed. **Example:** `/moderate`
* `/begin` - Begin a debate. Can only be used during the reconnaissance phase. Can only be used by the moderator after a debate has been proposed. Once sent, debaters can then submit their arguments. **Example:** `/begin`
* `/cancel` - Cancel a debate without posting a survey. Only a moderator can cancel the debate. If debaters use this command, this will count towards a vote and the debate will be cancelled if the majority of members in the group use this command. **Example:** `/cancel`
* `/conclude` - Conclude a debate gracefully and to send a survey after the debate concludes. Use this command when you have no more arguments to supply and would like to see how people's opinions have changed. Only a moderator can conclude the debate. If debaters use this command, this will count towards a vote and the debate will be conclude if the majority of members in the group use this command. **Example:** `/conclude`
* `/for <argument>` - Tag that's used to signify a supporting argument to the proposition. **Example:** `/for Pies have crusts making them easier to handle`
* `/against <argument>` - Tag that's used to signify an opposing argument to the proposition. **Example:** `/against Pies tend to be dryer than cake`
* `/meta <comment>` - Tag that's used to signify a comment being made that's not relevant to the proposition, usually directed at the moderator. Please use this as sparingly as possible. **Example:** `/meta A few people have forgotton to use the /for or /against tags in their arguments`
* `/poi <question>` - Tag that's used to ask questions or request information during a debate (stands for point of information). This should not be used to post rhetorical questions. **Example:** `/poi Do all pies have crusts?`
* `/lf <fallacy>` - Tag to signify that a logical fallacy has been used in one of the arguments. Please reply to the argument that you believe uses the logical fallacy. The moderator should pick up on this and ultimately decide if this logical fallacy was indeed used. **Example:** `/lf sarcasm`

## Structure of debates

Debotbot enforces the following structure to debates:

1. Debate initiated with a proposoition using `/debate <proposition>`. The person who sends this message is called the [**proposer**](#roles).
2. [**Moderator**](#roles) is nominated and selected
3. [**Debaters**](#roles) enter a reconneissance phase where they are encouraged to ask questions to the proposer to clarify their proposition. The proposer should be the only one answering the questions at this stage. The moderator is encouraged to moderate the flow of questions, notify the proposer if they've missed out any questions or if any questions are unclear.
4. The moderator can begin the debate once everyone has concluded their questioning
5. Debate phase begins - debaters should be using only any one of these commands during this stage: `/meta`, `/for`, `/against`, `/poi`, `/lf`, `/cancel` or `/conclude`
6. Debate can be conclude or be cancelled by popular vote or by the moderator at any time. A concluded debate differs from a cancelled debate in that it resembles that all parties have satisfied their arguments and are willing to bring the debate to a natural close. A cancelled debate is one that has not naturally closed and is either terminated due to an unclear proposition or due to a devolution of discussion.

## Roles

* **Proposer** - the person who proposes a debate using the `/debate` command
* **Moderator** - the person who has been selected as a moderator by Debotbot. First person to send a `/moderate` command after a debate has been proposed will be selected as the moderator. This person is not allowed to argue for or against the proposition. Their responsibility is to ensure people follow the rules and to ultimately make the decision on whether logical fallacies have been used in arguments. If a logical fallacy has been used, the moderator is encouraged to help the debater correct their argument where necessary. The moderator should:
  * Be as neutral as possible
  * Assume the best intentions from everyone
  * Educate as kindly as possible
* **Debater** - a member of the group who participates in a debate

## Logical fallacies

TBC

## Contributing

TBC

## Deploying

To run your own version of Debotbot, you can run the following commands (make sure you have Docker installed):

```sh
docker run -it --rm -e TG_API_TOKEN=<your API token here> sansaid/debotbot:latest
```
