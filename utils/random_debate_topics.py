import random

DEBATE_TOPICS = [
    'Wiping while sitting is better than standing',
    'Waxing is better than shaving',
    'It\'s not unhygienic to use the rubber gloves you clean the toilet with to clean your dishes',
    'Overhanging is better than underhanging your toilet roll',
    'Pies are better than cake'
]

def get_random_topic(debate_topics=DEBATE_TOPICS):
    max_topic_int = len(debate_topics) - 1
    index = random.randint(0, max_topic_int)

    return debate_topics[index]