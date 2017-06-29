"""
Puzzle Prison Game for Amazon Alexa by Benjamin Dring
"""

from __future__ import print_function
import time
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

# --------------- Locale

def locale_gb():
    return locale == "en-GB"

def locale_us():
    return locale == "en-US"

def locale_de():
    return locale == "de-DE"

# --------------- Audio

def create_audio_tag(file_name):
    return '<audio src="' + file_name + '"/>'

def audio_letter_box():
    if (locale_gb()):
        return "https://s3-eu-west-1.amazonaws.com/eu.puzzleprison.resources/LetterBox.mp3"
    else:
        return "https://s3.amazonaws.com/us.puzzleprison.resources/LetterBox.mp3"

def audio_sharp_click():
    if (locale_gb()):
        return "https://s3-eu-west-1.amazonaws.com/eu.puzzleprison.resources/SharpClick.mp3"
    else:
        return "https://s3.amazonaws.com/us.puzzleprison.resources/SharpClick.mp3"

def audio_moving_wall():
    if (locale_gb()):
        return "https://s3-eu-west-1.amazonaws.com/eu.puzzleprison.resources/MovingWall.mp3"
    else:
        return "https://s3.amazonaws.com/us.puzzleprison.resources/MovingWall.mp3"

def audio_moving_statue():
    if (locale_gb()):
        return "https://s3-eu-west-1.amazonaws.com/eu.puzzleprison.resources/MovingStatue.mp3"
    else:
        return "https://s3.amazonaws.com/us.puzzleprison.resources/MovingStatue.mp3"

def audio_computer_beeping():
    if (locale_gb()):
        return "https://s3-eu-west-1.amazonaws.com/eu.puzzleprison.resources/Beeps.mp3"
    else:
        return "https://s3.amazonaws.com/us.puzzleprison.resources/Beeps.mp3"

def audio_jingle():
    if (locale_gb()):
        return "https://s3-eu-west-1.amazonaws.com/eu.puzzleprison.resources/FinishJingle.mp3"
    else:
        return "https://s3.amazonaws.com/us.puzzleprison.resources/FinishJingle.mp3"

# --------------- Response building

def build_speech_response(title, output_speech, output_card, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'SSML',
            'ssml': '<speak>' + output_speech + '</speak>'
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': output_card
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }

def build_response(session_attributes, text, should_end_session = False):
    output_speech = text[1]
    output_card = text[1]
    if len(text) > 3:
        clip_index = 0
        while (clip_index < len(text) - 3):
            output_speech = output_speech.replace("&at", create_audio_tag(text[3 + clip_index]), 1)
            output_card = output_card.replace("&at", "", 1)
            clip_index += 1

    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': build_speech_response(text[0], output_speech, output_card, text[2], should_end_session)
    }

# --------------- Database

def PutQuestPoint(session):
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('PuzzlePrison')
        userId = session['user']['userId']
        table.put_item(
            Item={
                'userID': userId,
                'questPoint': 0,
                'lastUpdate': time.strftime("%Y-%m-%d")
            }
        )
    except ClientError as e1:
        print('Failed Database Access')

def SaveQuestPoint(session, qp):
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('PuzzlePrison')
        userId = session['user']['userId']
        response = table.update_item(
            Key={
                'userID': userId
            },
            UpdateExpression="set questPoint=:q, lastUpdate=:u",
            ExpressionAttributeValues={
                ':q': qp,
                ':u': time.strftime("%Y-%m-%d")
            },
            ReturnValues = "UPDATED_NEW"
        )
    except ClientError as e:
        print('Update Failed')

def LoadQuestPoint(session):
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('PuzzlePrison')
        userId = session['user']['userId']
        response = table.get_item(
            Key={
                'userID': userId
            }
        )
        if (len(response) < 2):
            PutQuestPoint(session)
            return 0
        else:
            item = response['Item']
            qp = item['questPoint']
            if (qp < 0 or qp > 10):
                SaveQuestPoint(session, 0)
                return 0
            else:
                return qp
    except ClientError as e1:
        try:
            PutQuestPoint(session)
            return 0
        except ClientError as e2:
            return 0

# --------------- Custom Slots

def get_object_slot(intent):
    if intent.get('slots', {}) and 'object' in intent['slots'] and 'value' in intent['slots']['object']:
        return intent['slots']['object']['value']
    else:
        return ""

def get_option_slot(intent):
    if intent.get('slots', {}) and 'option' in intent['slots'] and 'value' in intent['slots']['option']:
        return intent['slots']['option']['value']
    else:
        return ""

# --------------- Attributes

def get_attr(session, attr, default):
    if session.get('attributes', {}) and attr in session.get('attributes', {}):
        return session['attributes'][attr]
    else:
        return default

def get_quest_point(session):
    return get_attr(session, "QuestPoint", LoadQuestPoint(session))

def get_diag_order(session):
    return get_attr(session, "DiagProgress", "")

def get_ne_complete(session):
    return get_attr(session, "NE", False)

def get_nw_complete(session):
    return get_attr(session, "NW", False)

def get_se_complete(session):
    return get_attr(session, "SE", False)

def get_sw_complete(session):
    return get_attr(session, "SW", False)

def get_context(session):
    return get_attr(session, "Context", "")

def get_is_playing(session):
    return get_attr(session, "IsPlaying", False)

def build_attr(qp, diag, NE, NW, SE, SW, context):
    if (qp == 4):
        return{
            "QuestPoint": qp,
            "DiagProgress": diag,
            "Context": context,
            "IsPlaying": True,
        }
    elif (qp == 6):
        return {
            "QuestPoint": qp,
            "NE": NE,
            "NW": NW,
            "SE": SE,
            "SW": SW,
            "Context": context,
            "IsPlaying": True,
        }
    else:
        return {
            "QuestPoint": qp,
            "Context": context,
            "IsPlaying": True,
        }

# --------------- Texts Utility

def text_prompt():
    return "What would you like to do?"

def text_misunderstand():
    return "Sorry, I didn't understand what you said. Say, help, to receive a list of possible commands. "

def text_error():
    return "Sorry something went wrong"

def text_terminal_prompt():
    return "Which terminal?"

def text_statue_prompt():
    return "Which statue?"

def text_wall_prompt():
    return "Which wall?"

def text_options_prompt():
    return "Which option do you choose? One or two?"

# --------------- Texts Titles

def text_title_misunderstand():
    return "I didn't understand"

def text_title_error():
    return "Something went wrong"

def text_title_play_again():
    return "You are already playing"

def text_title_start_qp0():
    return "Welcome to Puzzle Prison"

def text_title_start():
    return "Welcome back to Puzzle Prison"

def text_title_stop():
    return "Thank you for playing!"

def text_title_walk_only_terminal():
    return "Walk to Computer Terminal"

def text_title_walk_northeast_terminal():
    return "Walk to North East Terminal"

def text_title_walk_northwest_terminal():
    return "Walk to North West Terminal"

def text_title_walk_southeast_terminal():
    return "Walk to South East Terminal"

def text_title_walk_southwest_terminal():
    return "Walk to South West Terminal"

def text_title_walk_central_terminal():
    return "Walk to Central Terminal"

def text_title_walk_northeast_statue():
    return "Walk to North East Statue"

def text_title_walk_northwest_statue():
    return "Walk to North West Statue"

def text_title_walk_southeast_statue():
    return "Walk to South East Statue"

def text_title_walk_southwest_statue():
    return "Walk to South West Statue"

def text_title_walk_north_wall():
    return "Walk to North Wall"

def text_title_walk_south_wall():
    return "Walk to South Wall"

def text_title_walk_east_wall():
    return "Walk to East Wall"

def text_title_walk_west_wall():
    return "Walk to West Wall"

def text_title_walk_letter():
    return "Walk to Letter"

def text_title_walk_letter_box():
    return "Walk to Letter Box"

def text_title_walk_metal_cabinet():
    return "Walk to Metal Cabinet"

def text_title_only_computer_terminal_qp0():
    return "Using the computer terminal"

def text_title_northeast_computer_terminal_qp6():
    return "You use the north east terminal"

def text_title_northwest_computer_terminal_qp6():
    return "You use the north west terminal"

def text_title_southeast_computer_terminal_qp6():
    return "You use the south east terminal"

def text_title_southwest_computer_terminal_qp6():
    return "You use the south west terminal"

def text_title_computer_terminal_not_responding():
    return "The computer is not responding"

def text_title_interact_statue():
    return "You examine the statue"

def text_title_interact_north_wall_qp2():
    return "You Push the North Wall"

def text_title_interact_north_wall():
    return "Knock on North Wall"

def text_title_interact_south_wall():
    return "Knock on South Wall"

def text_title_interact_east_wall():
    return "Knock on East Wall"

def text_title_interact_west_wall():
    return "Knock on West Wall"

def text_title_interact_letter_box():
    return "You look through the letter box"

def text_title_interact_metal_cabinet():
    return "You attempt to open the metal cabinet"

def text_title_read_letter():
    return "You read the letter"

def text_title_nice_option():
    return "The computer seems happy"

def text_title_mean_option():
    return "You've upset the computer, it's stopped working"

# --------------- Texts Walk To Non Special

def text_walk_to_wall():
    return "Which wall would you like to walk to? Your options are north, south, east and west."

def text_walk_to_north_wall():
    return "You walk up to the north most wall. " +\
           text_prompt()

def text_walk_to_south_wall():
    return "You walk up to the south most wall. " +\
           text_prompt()

def text_walk_to_east_wall():
    return "You walk up to the east most wall. " +\
           text_prompt()

def text_walk_to_west_wall():
    return "You walk up to the west most wall. " +\
           text_prompt()

def text_walk_to_statue():
    return "Which statue would you like to walk to? Your options are north east, north west, " \
           "south east and south west."

def text_walk_to_northeast_statue():
    return "You walk up to the statue in the north east corner. " +\
           text_prompt()

def text_walk_to_northwest_statue():
    return "You walk up to the statue in the north west corner. " +\
           text_prompt()

def text_walk_to_southeast_statue():
    return "You walk up to the statue in the south east corner. " +\
           text_prompt()

def text_walk_to_southwest_statue():
    return "You walk up to the statue in the south west corner. " +\
           text_prompt()

def text_walk_to_terminal():
    return "Which Terminal would you like to walk to? Your options are north east, north west, " \
           "south east and south west."

def text_walk_to_northeast_computer_terminal():
    return "You walk up to the computer terminal in the north east corner. " +\
           text_prompt()

def text_walk_to_northwest_computer_terminal():
    return "You walk up to the computer terminal in the north west corner. " +\
           text_prompt()

def text_walk_to_southeast_computer_terminal():
    return "You walk up to the computer terminal in the south east corner. " +\
           text_prompt()

def text_walk_to_southwest_computer_terminal():
    return "You walk up to the computer terminal in the south west corner. " +\
           text_prompt()

def text_walk_to_central_computer_terminal():
    return "You walk up to the computer terminal in the centre of the room. " +\
           text_prompt()

def text_walk_to_only_computer_terminal():
    return "You walk up to the computer terminal. " +\
           text_prompt()

def text_walk_to_letter_box():
    return "You walk up to the letter box in the south most wall. " +\
           text_prompt()

def text_walk_to_metal_cabinet():
    return "You walk up to the metal cabinet beneath the computer terminal. " +\
           text_prompt()

# --------------- Texts Walk To Special

def text_walk_to_qp4_end_northeast_statue():
    return "You walk up to the statue in the north east corner. " \
           "You see a red flash from the eyes of the raven statue. " \
           "&atYou hear a noise and see a letter fall through the letter box. " +\
           text_prompt()

def text_walk_to_qp4_end_northwest_statue():
    return "You walk up to the statue in the north west corner. " \
           "You see a red flash from the eyes of the raven statue. " \
           "&atYou hear a noise and see a letter fall through the letter box. " +\
           text_prompt()

def text_walk_to_qp4_end_southeast_statue():
    return "You walk up to the statue in the south east corner. " \
           "You see a red flash from the eyes of the raven statue. " \
           "&atYou hear a noise and see a letter fall through the letter box. " +\
           text_prompt()

def text_walk_to_qp4_end_southwest_statue():
    return "You walk up to the statue in the south west corner. " \
           "You see a red flash from the eyes of the raven statue. " \
           "&atYou hear a noise and see a letter fall through the letter box. " +\
           text_prompt()

# --------------- Texts Interact Non Special

def text_interact_wall():
    return "Which wall would you like to interact with? Your options are north, south, east and west."

def text_interact_north_wall():
    return "You knock on the north wall, the wall seems to be solid brick, you couldn't find any secrets. " +\
           text_prompt()

def text_interact_south_wall():
    return "You knock on the south wall, the wall seems to be solid brick, you couldn't find any secrets. " +\
           text_prompt()

def text_interact_east_wall():
    return "You knock on the east wall, the wall seems to be solid brick, you couldn't find any secrets. " +\
           text_prompt()

def text_interact_west_wall():
    return "You knock on the west wall, the wall seems to be solid brick, you couldn't find any secrets. " +\
           text_prompt()

def text_interact_statue():
    return "Which statue would you like to interact with? Your options are north east, north west, " \
           "south east and south west."

def text_interact_northeast_statue():
    return "You knock on the north east statue, it appears to be hollow inside. " \
           "You run your hand across the surface and find a seam. " \
           "You try to open the statue at the seam but some sort of hidden locking mechanism is stopping you. " +\
           text_prompt()

def text_interact_northwest_statue():
    return "You knock on the north west statue, it appears to be hollow inside. " \
           "You run your hand across the surface and find a seam. " \
           "You try to open the statue at the seam but some sort of hidden locking mechanism is stopping you. " +\
           text_prompt()

def text_interact_southeast_statue():
    return "You knock on the south east statue, it appears to be hollow inside. " \
           "You run your hand across the surface and find a seam. " \
           "You try to open the statue at the seam but some sort of hidden locking mechanism is stopping you. " +\
           text_prompt()

def text_interact_southwest_statue():
    return "You knock on the south west statue, it appears to be hollow inside. " \
           "You run your hand across the surface and find a seam. " \
           "You try to open the statue at the seam but some sort of hidden locking mechanism is stopping you. " +\
           text_prompt()

def text_interact_terminal():
    return "Which Terminal would you like to interact with? Your options are north east, north west, " \
            "south east and south west."

def text_interact_northeast_computer_terminal():
    return "You attempt to use the north east computer terminal, the computer seems to be not responding, " \
           "you can't find anyway to fix it. " +\
           text_prompt()

def text_interact_northwest_computer_terminal():
    return "You attempt to use the north west computer terminal, the computer seems to be not responding, " \
           "you can't find anyway to fix it. " +\
           text_prompt()

def text_interact_southeast_computer_terminal():
    return "You attempt to use the south east computer terminal, the computer seems to be not responding, " \
           "you can't find anyway to fix it. " +\
           text_prompt()

def text_interact_southwest_computer_terminal():
    return "You attempt to use the south west computer terminal, the computer seems to be not responding, " \
           "you can't find anyway to fix it. " +\
           text_prompt()

def text_interact_central_computer_terminal():
    return "You attempt to use the central computer terminal, the computer seems to be not responding, " \
           "you can't find anyway to fix it. " +\
           text_prompt()

def text_interact_only_computer_terminal():
    return "You attempt to use the computer terminal, the computer seems to be not responding, " \
           "you can't find anyway to fix it. " +\
           text_prompt()

def text_interact_letter_box():
    return "You kneel down, open the letter box and peer through. " \
           "All you see is dark emptiness, it gives you the creeps so you close the letter box. " +\
           text_prompt()

def text_interact_metal_cabinet():
    return "You attempt to open the metal cabinet. " \
           "The cabinet is locked and the lock is stronger than it appears. " \
           "You can't break the lock. " +\
           text_prompt()

# --------------- Texts Interact Special

def text_interact_north_wall_qp2():
    return "You knock on the north wall, you notice that the wall has some give to it. " \
           "You give the north wall a firm push and it starts moving.&at " \
           "The northeast and northwest statues move with the wall but the computer terminal remains. " \
           "The wall locks into place leaving the room square and the computer terminal in the very centre. " \
           "&atYou hear a noise and see a letter fall through the letter box. " +\
           text_prompt()

def text_interact_northeast_computer_terminal_qp6():
    return "You press a button on the north east computer terminal and some text appears, it reads, " \
           "I hope to be a great father someday. " \
           "Two options appear on screen. " \
           "One. " \
           "I'm sure you will. " \
           "And two. " \
           "You will never have children. " \
           "Which option would you like to choose? Option one or two?"

def text_interact_northwest_computer_terminal_qp6():
    return "You press a button on the north west computer terminal and some text appears, it reads, " \
           "I want to be remembered, looked back upon as part of history. " \
           "Two options appear on screen. " \
           "One. " \
           "Your grave will hold a meaningless name. " \
           "And two. " \
           "With enough work, you can do this. " \
           "Which option would you like to choose? Option one or two?"

def text_interact_southeast_computer_terminal_qp6():
    return "You press a button on the south east computer terminal and some text appears, it reads, " \
           "As long as I can continue helping people, I will be happy. " \
           "Two options appear on screen. " \
           "One. " \
           "A helping hand is always needed. " \
           "And two. " \
           "You can't even help yourself. " \
           "Which option would you like to choose? Option one or two?"

def text_interact_southwest_computer_terminal_qp6():
    return "You press a button on the south west computer terminal and some text appears, it reads, " \
           "I want to create something brand new and advance mankind. " \
           "Two options appear on screen. " \
           "One. " \
           "Everything that can be done, has already been done. " \
           "And two. " \
           "Think outside the box, I believe in you. " \
           "Which option would you like to choose? Option one or two?"

def text_interact_northeast_computer_terminal_qp6_help():
    return "Two options appear on screen. " \
           "One. " \
           "I'm sure you will. " \
           "And two. " \
           "You will never have children. " \
           "Say, one, to select option one. Say, two, to select option two."

def text_interact_northwest_computer_terminal_qp6_help():
    return "Two options appear on screen. " \
           "One. " \
           "Your grave will hold a meaningless name. " \
           "And two. " \
           "With enough work, you can do this. " \
           "Say, one, to select option one. Say, two, to select option two."

def text_interact_southeast_computer_terminal_qp6_help():
    return "Two options appear on screen. " \
           "One. " \
           "A helping hand is always needed. " \
           "And two. " \
           "You can't even help yourself. " \
           "Say, one, to select option one. Say, two, to select option two."

def text_interact_southwest_computer_terminal_qp6_help():
    return "Two options appear on screen. " \
           "One. " \
           "Everything that can be done, has already been done. " \
           "And two. " \
           "Think outside the box, I believe in you. " \
           "Say, one, to select option one. Say, two, to select option two."

def text_interact_only_computer_terminal_qp0():
    return "You press a button on the computer terminal and some text appears, it reads, " \
           "Escape your prison. " \
           "The computer seems to have stopped responding to your input. " \
           "&atYou hear a noise and see a letter fall through the letter box. " \
           "Say read, to read the letter. " +\
           text_prompt()

# --------------- Texts Options

def text_option_northeast_computer_terminal_a():
    return "Text appears on the screen. It reads, " \
           "Thank you so much for your support. " \
           "A pixelated smiley face appears on screen. "

def text_option_northeast_computer_terminal_b():
    return "Text appears on the screen. It reads, " \
           "I feel awful! Why would you say that? " \
           "A pixelated sad face appears on screen, " \
           "the computer terminal seems to have stopped responding. "

def text_option_northwest_computer_terminal_a():
    return "Text appears on the screen. It reads, " \
           "That is my greatest fear, I cannot cope with that. " \
           "A pixelated sad face appears on screen, "

def text_option_northwest_computer_terminal_b():
    return "Text appears on the screen. It reads, " \
           "I will work my hardest, thank you. " \
           "A pixelated smiley face appears on screen. "

def text_option_southeast_computer_terminal_a():
    return "Text appears on the screen. It reads, " \
           "I believe so too, if you need anything let me know. " \
           "A pixelated smiley face appears on screen. "

def text_option_southeast_computer_terminal_b():
    return "Text appears on the screen. It reads, " \
           "Why must I be punished for my selflessness? " \
           "A pixelated sad face appears on screen, " \
           "the computer terminal seems to have stopped responding. "

def text_option_southwest_computer_terminal_a():
    return "Text appears on the screen. It reads, " \
           "I'm not unique. what is the point of anything? " \
           "A pixelated sad face appears on screen, " \
           "the computer terminal seems to have stopped responding. "

def text_option_southwest_computer_terminal_b():
    return "Text appears on the screen. It reads, " \
           "Thank you so much, have a great day! " \
           "A pixelated smiley face appears on screen. "

def text_option_non_end_northeast_computer_terminal_a():
    return text_option_northeast_computer_terminal_a() + \
           text_prompt()

def text_option_non_end_northeast_computer_terminal_b():
    return text_option_northeast_computer_terminal_b() + \
           text_prompt()

def text_option_non_end_northwest_computer_terminal_a():
    return text_option_northwest_computer_terminal_a() + \
           text_prompt()

def text_option_non_end_northwest_computer_terminal_b():
    return text_option_northwest_computer_terminal_b() + \
           text_prompt()

def text_option_non_end_southeast_computer_terminal_a():
    return text_option_southeast_computer_terminal_a() + \
           text_prompt()

def text_option_non_end_southeast_computer_terminal_b():
    return text_option_southeast_computer_terminal_b() + \
           text_prompt()

def text_option_non_end_southwest_computer_terminal_a():
    return text_option_southwest_computer_terminal_a() + \
           text_prompt()

def text_option_non_end_southwest_computer_terminal_b():
    return text_option_southwest_computer_terminal_b() + \
           text_prompt()

def text_option_end_northeast_computer_terminal_b():
    return text_option_northeast_computer_terminal_b() + \
           "All the corner computers start making beeping noises.&at " \
           "&atYou hear a noise and see a letter fall through the letter box. " + \
           text_prompt()

def text_option_end_northwest_computer_terminal_a():
    return text_option_northwest_computer_terminal_a() + \
           "All the corner computers start making beeping noises.&at " \
           "&atYou hear a noise and see a letter fall through the letter box. " + \
           text_prompt()

def text_option_end_southeast_computer_terminal_b():
    return text_option_southeast_computer_terminal_b() + \
           "All the corner computers start making beeping noises.&at " \
           "&atYou hear a noise and see a letter fall through the letter box. " + \
           text_prompt()

def text_option_end_southwest_computer_terminal_a():
    return text_option_southwest_computer_terminal_a() + \
           "All the corner computers start making beeping noises.&at " \
           "&atYou hear a noise and see a letter fall through the letter box. " + \
           text_prompt()

# --------------- Texts Letters

def text_interact_letter_qp2():
    return "You bend down and pick up the letter. It reads, " \
           "Better yourself, push your boundaries. " +\
           text_prompt()

def text_interact_letter_qp4():
    return "You bend down and pick up the latest letter. It reads, " \
           "Prepare yourself, take a lap to clear your head. " +\
           text_prompt()

def text_interact_letter_qp6():
    return "You bend down and pick up the latest letter. It reads, " \
           "Frame yourself, act uncharacteristically for perspective. " +\
           text_prompt()

def text_interact_letter_qp8():
    return "You bend down and pick up the latest letter. It reads, " \
           "Remove yourself, take a break from what you're doing. " +\
           text_prompt()

def text_interact_letter_qp2_first_time():
    return "You bend down and pick up the letter. It reads, " \
           "Better yourself, push your boundaries. " \
           "&atYou hear a sharp click but you can't tell where it came from. " +\
           text_prompt()

def text_interact_letter_qp6_first_time():
    return "You bend down and pick up the latest letter. It reads, " \
           "Frame yourself, act uncharacteristically for perspective. " \
           "Suddenly the four statues starting moving loudly&at, they unfurled revealing four computer terminals in " \
           "northeast, southeast, northwest and southwest corners of the room. " +\
           text_prompt()

def text_end():
    if locale_gb():
        return "You bend down and pick up the latest letter. It reads, " \
               "Believe in yourself, it's time to go. " \
               "You hear a noise, the cabinet under the central computer terminal opens, " \
               "revealing a ladder leading underground. " \
               "You start climbing down but your foot slips. " \
               "You tumble down the ladder, although bewildered, you are unharmed. " \
               "You look around to find yourself on the floor of your own house, " \
               "a ladder leading up to your loft rests in front of you. " \
               "You look up the ladder to find the room nowhere to be found. " \
               "You suddenly remember that you've got an exam to sit, you forget about the room and start getting ready. " \
               "The end. " \
               "Please let people know what you thought by leaving a review of the skill on the Amazon store. " \
               "Thank you for playing Puzzle Prison.&at "
    else:
        return "You bend down and pick up the latest letter. It reads, " \
               "Believe in yourself, it's time to go. " \
               "You hear a noise, the cabinet under the central computer terminal opens, " \
               "revealing a ladder leading underground. " \
               "You start climbing down but your foot slips. " \
               "You tumble down the ladder, although bewildered, you are unharmed. " \
               "You look around to find yourself on the floor of your own house, " \
               "a ladder leading up to your attic rests in front of you. " \
               "You look up the ladder to find the room nowhere to be found. " \
               "You suddenly remember that you've got an exam to sit, you forget about the room and start getting ready. " \
               "The end. " \
               "Please let people know what you thought by leaving a review of the skill on the Amazon store. " \
               "Thank you for playing Puzzle Prison.&at "

# --------------- Texts Events and Help

def text_instructions():
    return "Say, walk to, followed by something in the room to move towards that object. " \
           "Say, interact with, followed by something in the room to use that object. " \
           "Say help, to hear these instructions again at any point during the game. " \
           "Say repeat, to get an overview of the room and say stop, to stop playing. "

def text_instructions_first_time():
    return text_instructions()

def text_play_again():
    return "You are already playing. To restart say, replay. For instructions on how to play say, help. " +\
           text_prompt()

def text_play_again_options():
    return "You are already playing. To restart say, replay. For instructions on how to play say, help. " +\
           text_options_prompt()

def text_qp0_start():
    return "Welcome to puzzle prison. " + \
           text_instructions_first_time() + \
           "The room has four walls but no doors. " \
           "The room is rectangular with the east and west walls half the length of the north and south walls. " \
           "There are four raven statues in the northeast, northwest, southeast and southwest corners of the room. " \
           "A single computer terminal resting atop a locked metal cabinet sits beside the centre of the north wall. " \
           "In the centre of the south wall resides a single letter box. " +\
           text_prompt()

def text_qp0_overview():
    return "You are in a rectangular room with four walls north, south, east and west. " \
           "There are four raven statues in the northeast, northwest, southeast and southwest corners of the room. " \
           "A computer terminal resting atop a locked metal cabinet sits beside the centre of the north wall. " \
           "In the centre of the south wall resides a single letter box. " +\
           text_prompt()

def text_qp0_repeat():
    return "You awake to find yourself in a room. " + \
           text_qp0_overview()

def text_qp0_help():
    return text_instructions() + \
           text_qp0_overview()

def text_qp1_overview():
    return "You are in a rectangular room with four walls north, south, east and west. " \
           "There are four raven statues in the northeast, northwest, southeast and southwest corners of the room. " \
           "A computer terminal resting atop a locked metal cabinet sits beside the centre of the north wall. " \
           "In the centre of the south wall resides a single letter box. " \
           "A letter has just been posted through the box and rests on the floor. " +\
           text_prompt()

def text_qp1_start():
    return "Welcome back to puzzle prison. " + \
           text_qp1_overview()

def text_qp1_repeat():
    return text_qp1_overview()

def text_qp1_help():
    return text_instructions() + \
           text_qp1_overview()

def text_qp2_overview():
    return text_qp1_overview()

def text_qp2_start():
    return "Welcome back to puzzle prison. " + \
           text_qp2_overview()

def text_qp2_repeat():
    return text_qp2_overview()

def text_qp2_help():
    return text_instructions() + \
           text_qp2_overview()

def text_qp3_overview():
    return "You are in a square room with four walls north, south, east and west. " \
           "There are four raven statues in the northeast, northwest, southeast and southwest corners of the room. " \
           "A computer terminal resting atop a locked metal cabinet sits in the centre of the room. " \
           "In the centre of the south wall resides a single letter box. " \
           "A letter has just been posted through the box and rests on the floor. " +\
           text_prompt()

def text_qp3_start():
    return "Welcome back to puzzle prison. " + \
           text_qp3_overview()

def text_qp3_repeat():
    return text_qp3_overview()

def text_qp3_help():
    return text_instructions() + \
           text_qp3_overview()

def text_qp4_overview():
    return text_qp3_overview()

def text_qp4_start():
    return "Welcome back to puzzle prison. " + \
           text_qp4_overview()

def text_qp4_repeat():
    return text_qp4_overview()

def text_qp4_help():
    return text_instructions() + \
           text_qp4_overview()

def text_qp5_overview():
    return text_qp3_overview()

def text_qp5_start():
    return "Welcome back to puzzle prison. " + \
           text_qp5_overview()

def text_qp5_repeat():
    return text_qp5_overview()

def text_qp5_help():
    return text_instructions() + \
           text_qp5_overview()

def text_qp6_overview():
    return "You are in a square room with four walls north, south, east and west. " \
           "There are four computer terminals in the northeast, northwest, southeast and southwest corners of the room. " \
           "A fifth computer terminal resting atop a locked metal cabinet sits in the centre of the room. " \
           "In the centre of the south wall resides a single letter box. " \
           "A letter has just been posted through the box and rests on the floor. " +\
           text_prompt()

def text_qp6_start():
    return "Welcome back to puzzle prison. " + \
           text_qp6_overview()

def text_qp6_repeat():
    return text_qp6_overview()

def text_qp6_help():
    return text_instructions() + \
           text_qp6_overview()

def text_qp7_overview():
    return text_qp6_overview()

def text_qp7_start():
    return "Welcome back to puzzle prison. " + \
           text_qp7_overview()

def text_qp7_repeat():
    return text_qp7_overview()

def text_qp7_help():
    return text_instructions() + \
           text_qp7_overview()

def text_qp8_overview():
    return text_qp6_overview()

def text_qp8_start():
    return "Welcome back to puzzle prison. " \
           "You awake from a well deserved break and look around the square room. " \
           "&atYou hear a noise and see a letter fall through the letter box. " +\
           text_prompt()

def text_qp8_repeat():
    return text_qp8_overview()

def text_qp8_help():
    return text_instructions() + \
           text_qp8_overview()

def text_qp9_overview():
    return text_qp6_overview()

def text_qp9_start():
    return "Welcome back to puzzle prison. " + \
           text_qp9_overview()

def text_qp9_repeat():
    return text_qp9_overview()

def text_qp9_help():
    return text_instructions() + \
           text_qp9_overview()

def text_stop():
    return "Your progress has been saved. Thank you for playing.&at"

# --------------- Diag

def update_diag(diag, update):
    if len(diag) == 0:
        return update
    elif diag.endswith(update):
        return diag
    elif update in diag:
        return ""
    elif diag.endswith("A"):
        if update == "C":
            return ""
        else:
            return (diag + update)
    elif diag.endswith("B"):
        if update == "D":
            return ""
        else:
            return (diag + update)
    elif diag.endswith("C"):
        if update == "A":
            return ""
        else:
            return (diag + update)
    elif diag.endswith("D"):
        if update == "B":
            return ""
        else:
            return (diag + update)
    else:
        return ""

def update_lap(diag, update):
    diag = update_diag(diag, update)

    if len(diag) >= 4:
        return [True, ""]
    else:
        return [False, diag]

# --------------- Intent Events

def misunderstand_response(attr):
    return build_response(
        attr,
        [
            text_title_misunderstand(),
            text_misunderstand(),
            ""
        ]
    )

def error_response():
    return build_response(
        {},
        [
            text_title_error(),
            text_error(),
            ""
        ],
        False
    )

def on_intent_start(session):
    qp = get_quest_point(session)
    is_playing = get_is_playing(session)

    if is_playing:
        attr = session['attributes']
        if ("qp6_" in get_context(session)):
            return build_response(
                attr,
                [
                    text_title_play_again(),
                    text_play_again_options(),
                    text_options_prompt()
                ]
            )
        else:
            return build_response(
                attr,
                [
                    text_title_play_again(),
                    text_play_again(),
                    text_prompt()
                ]
            )
    elif qp == 0:
        return build_response(
            build_attr(0, "", False, False, False, False, ""),
            [
                text_title_start_qp0(),
                text_qp0_start(),
                text_prompt()
            ]
        )
    elif qp == 1:
        return build_response(
            build_attr(1, "", False, False, False, False, ""),
            [
                text_title_start(),
                text_qp1_start(),
                text_prompt()
            ]
        )
    elif qp == 2:
        return build_response(
            build_attr(2, "", False, False, False, False, ""),
            [
                text_title_start(),
                text_qp2_start(),
                text_prompt()
            ]
        )
    elif qp == 3:
        return build_response(
            build_attr(3, "", False, False, False, False, ""),
            [
                text_title_start(),
                text_qp3_start(),
                text_prompt()
            ]
        )
    elif qp == 4:
        return build_response(
            build_attr(4, "", False, False, False, False, ""),
            [
                text_title_start(),
                text_qp4_start(),
                text_prompt()
            ]
        )
    elif qp == 5:
        return build_response(
            build_attr(5, "", False, False, False, False, ""),
            [
                text_title_start(),
                text_qp5_start(),
                text_prompt()
            ]
        )
    elif qp == 6:
        return build_response(
            build_attr(6, "", False, False, False, False, ""),
            [
                text_title_start(),
                text_qp6_start(),
                text_prompt()
            ]
        )
    elif qp == 7:
        return build_response(
            build_attr(7, "", False, False, False, False, ""),
            [
                text_title_start(),
                text_qp7_start(),
                text_prompt()
            ]
        )
    elif qp == 8:
        SaveQuestPoint(session, 9)
        return build_response(
            build_attr(9, "", False, False, False, False, ""),
            [
                text_title_start(),
                text_qp8_start(),
                text_prompt(),
                audio_letter_box()
            ]
        )
    elif qp == 9:
        return build_response(
            build_attr(9, "", False, False, False, False, ""),
            [
                text_title_start(),
                text_qp9_start(),
                text_prompt()
            ]
        )
    else:
        return error_response()

def on_intent_help(session):
    qp = get_quest_point(session)
    attr = session['attributes']

    if qp == 0:
        return build_response(
            attr,
            [
                text_prompt(),
                text_qp0_help(),
                text_prompt()
            ]
        )
    elif qp == 1:
        return build_response(
            attr,
            [
                text_prompt(),
                text_qp1_help(),
                text_prompt()
            ]
        )
    elif qp == 2:
        return build_response(
            attr,
            [
                text_prompt(),
                text_qp2_help(),
                text_prompt()
            ]
        )
    elif qp == 3:
        return build_response(
            attr,
            [
                text_prompt(),
                text_qp3_help(),
                text_prompt()
            ]
        )
    elif qp == 4:
        return build_response(
            attr,
            [
                text_prompt(),
                text_qp4_help(),
                text_prompt()
            ]
        )
    elif qp == 5:
        return build_response(
            attr,
            [
                text_prompt(),
                text_qp5_help(),
                text_prompt()
            ]
        )
    elif qp == 6:
        return build_response(
            attr,
            [
                text_prompt(),
                text_qp6_help(),
                text_prompt()
            ]
        )
    elif qp == 7:
        return build_response(
            attr,
            [
                text_prompt(),
                text_qp7_help(),
                text_prompt()
            ]
        )
    elif qp == 8:
        return build_response(
            attr,
            [
                text_prompt(),
                text_qp8_help(),
                text_prompt()
            ]
        )
    elif qp == 9:
        return build_response(
            attr,
            [
                text_prompt(),
                text_qp9_help(),
                text_prompt()
            ]
        )
    else:
        return error_response()

def on_intent_repeat(session):
    qp = get_quest_point(session)
    attr = session['attributes']

    if qp == 0:
        return build_response(
            attr,
            [
                text_prompt(),
                text_qp0_overview(),
                text_prompt()
            ]
        )
    elif qp == 1:
        return build_response(
            attr,
            [
                text_prompt(),
                text_qp1_overview(),
                text_prompt()
            ]
        )
    elif qp == 2:
        return build_response(
            attr,
            [
                text_prompt(),
                text_qp2_overview(),
                text_prompt()
            ]
        )
    elif qp == 3:
        return build_response(
            attr,
            [
                text_prompt(),
                text_qp3_overview(),
                text_prompt()
            ]
        )
    elif qp == 4:
        return build_response(
            attr,
            [
                text_prompt(),
                text_qp4_overview(),
                text_prompt()
            ]
        )
    elif qp == 5:
        return build_response(
            attr,
            [
                text_prompt(),
                text_qp5_overview(),
                text_prompt()
            ]
        )
    elif qp == 6:
        return build_response(
            attr,
            [
                text_prompt(),
                text_qp6_overview(),
                text_prompt()
            ]
        )
    elif qp == 7:
        return build_response(
            attr,
            [
                text_prompt(),
                text_qp7_overview(),
                text_prompt()
            ]
        )
    elif qp == 8:
        return build_response(
            attr,
            [
                text_prompt(),
                text_qp8_overview(),
                text_prompt()
            ]
        )
    elif qp == 9:
        return build_response(
            attr,
            [
                text_prompt(),
                text_qp9_overview(),
                text_prompt()
            ]
        )
    else:
        return error_response()

def on_intent_help_on_terminal(session):
    attr = session['attributes']
    context = get_context(session)

    if (context == "qp6_ne"):
        return build_response(
            attr,
            [
                text_options_prompt(),
                text_interact_northeast_computer_terminal_qp6_help(),
                text_options_prompt()
            ]
        )
    elif (context == "qp6_nw"):
        return build_response(
            attr,
            [
                text_options_prompt(),
                text_interact_northwest_computer_terminal_qp6_help(),
                text_options_prompt()
            ]
        )
    elif (context == "qp6_se"):
        return build_response(
            attr,
            [
                text_options_prompt(),
                text_interact_southeast_computer_terminal_qp6_help(),
                text_options_prompt()
            ]
        )
    elif (context == "qp6_sw"):
        return build_response(
            attr,
            [
                text_options_prompt(),
                text_interact_southwest_computer_terminal_qp6_help(),
                text_options_prompt()
            ]
        )
    else:
        return error_response()

def on_intent_repeat_on_terminal(session):
    attr = session['attributes']
    context = get_context(session)

    if (context == "qp6_ne"):
        return build_response(
            attr,
            [
                text_options_prompt(),
                text_interact_northeast_computer_terminal_qp6(),
                text_options_prompt()
            ]
        )
    elif (context == "qp6_nw"):
        return build_response(
            attr,
            [
                text_options_prompt(),
                text_interact_northwest_computer_terminal_qp6(),
                text_options_prompt()
            ]
        )
    elif (context == "qp6_se"):
        return build_response(
            attr,
            [
                text_options_prompt(),
                text_interact_southeast_computer_terminal_qp6(),
                text_options_prompt()
            ]
        )
    elif (context == "qp6_sw"):
        return build_response(
            attr,
            [
                text_options_prompt(),
                text_interact_southwest_computer_terminal_qp6(),
                text_options_prompt()
            ]
        )
    else:
        return error_response()

def on_intent_startover():
    return build_response(
        build_attr(0, "", False, False, False, False, ""),
        [
            text_title_start_qp0(),
            text_qp0_start(),
            text_prompt()
        ]
    )

def on_intent_stop():
    return build_response(
        {},
        [
            text_title_stop(),
            text_stop(),
            "",
            audio_jingle()
        ],
        True
    )

def on_intent_walk_terminal(session, obj):
    qp = get_quest_point(session)
    diag = get_diag_order(session)
    NE = get_ne_complete(session)
    NW = get_nw_complete(session)
    SE = get_se_complete(session)
    SW = get_sw_complete(session)
    attr = session['attributes']

    if qp < 6:
        return build_response(
            build_attr(qp, diag, NE, NW, SE, SW, "central terminal"),
            [
                text_title_walk_only_terminal(),
                text_walk_to_only_computer_terminal(),
                text_prompt()
            ]
        )
    elif (obj == "northeast terminal") or (obj == "northeast computer"):
        return build_response(
            build_attr(qp, diag, NE, NW, SE, SW, "northeast terminal"),
            [
                text_title_walk_northeast_terminal(),
                text_walk_to_northeast_computer_terminal(),
                text_prompt()
            ]
        )
    elif (obj == "northwest terminal") or (obj == "northwest computer"):
        return build_response(
            build_attr(qp, diag, NE, NW, SE, SW, "northwest terminal"),
            [
                text_title_walk_northwest_terminal(),
                text_walk_to_northwest_computer_terminal(),
                text_prompt()
            ]
        )
    elif (obj == "southeast terminal") or (obj == "southeast computer"):
        return build_response(
            build_attr(qp, diag, NE, NW, SE, SW, "southeast terminal"),
            [
                text_title_walk_southeast_terminal(),
                text_walk_to_southeast_computer_terminal(),
                text_prompt()
            ]
        )
    elif (obj == "southwest terminal") or (obj == "southwest computer"):
        return build_response(
            build_attr(qp, diag, NE, NW, SE, SW, "southwest terminal"),
            [
                text_title_walk_southwest_terminal(),
                text_walk_to_southwest_computer_terminal(),
                text_prompt()
            ]
        )
    elif (obj == "central terminal") or (obj == "central computer"):
        return build_response(
            build_attr(qp, diag, NE, NW, SE, SW, "central terminal"),
            [
                text_title_walk_central_terminal(),
                text_walk_to_central_computer_terminal(),
                text_prompt()
            ]
        )
    elif (obj == "terminal") or (obj == "computer") or (obj == "computer terminal"):
        return build_response(
            build_attr(qp, diag, NE, NW, SE, SW, get_context(session)),
            [
                text_terminal_prompt(),
                text_walk_to_terminal(),
                text_terminal_prompt()
            ]
        )
    else:
        return misunderstand_response(attr)

def on_intent_walk_statue(session, obj):
    qp = get_quest_point(session)
    diag = get_diag_order(session)
    NE = get_ne_complete(session)
    NW = get_nw_complete(session)
    SE = get_se_complete(session)
    SW = get_sw_complete(session)
    context = get_context(session)
    attr = session['attributes']

    if qp >= 6:
        return misunderstand_response(attr)
    elif (obj == "statue") or (obj == "raven"):
        return build_response(
            build_attr(qp, diag, NE, NW, SE, SW, context),
            [
                text_statue_prompt(),
                text_walk_to_statue(),
                text_statue_prompt()
            ]
        )
    elif (qp == 4):
        if (obj == "northeast statue") or (obj == "northeast raven"):
            [lap_done, diag] = update_lap(diag, "C")
            if (lap_done):
                SaveQuestPoint(session, qp + 1)
                return build_response(
                    build_attr(qp + 1, diag, NE, NW, SE, SW, "northeast statue"),
                    [
                        text_title_walk_northeast_statue(),
                        text_walk_to_qp4_end_northeast_statue(),
                        text_prompt(),
                        audio_letter_box()
                    ]
                )
            else:
                return build_response(
                    build_attr(qp, diag, NE, NW, SE, SW, "northeast statue"),
                    [
                        text_title_walk_northeast_statue(),
                        text_walk_to_northeast_statue(),
                        text_prompt()
                    ]
                )
        elif (obj == "northwest statue") or (obj == "northwest raven"):
            [lap_done, diag] = update_lap(diag, "B")
            if (lap_done):
                SaveQuestPoint(session, qp + 1)
                return build_response(
                    build_attr(qp + 1, diag, NE, NW, SE, SW, "northwest statue"),
                    [
                        text_title_walk_northwest_statue(),
                        text_walk_to_qp4_end_northwest_statue(),
                        text_prompt(),
                        audio_letter_box()
                    ]
                )
            else:
                return build_response(
                    build_attr(qp, diag, NE, NW, SE, SW, "northwest statue"),
                    [
                        text_title_walk_northwest_statue(),
                        text_walk_to_northwest_statue(),
                        text_prompt()
                    ]
                )
        elif (obj == "southeast statue") or (obj == "southeast raven"):
            [lap_done, diag] = update_lap(diag, "D")
            if (lap_done):
                SaveQuestPoint(session, qp + 1)
                return build_response(
                    build_attr(qp + 1, diag, NE, NW, SE, SW, "southeast statue"),
                    [
                        text_title_walk_southeast_statue(),
                        text_walk_to_qp4_end_southeast_statue(),
                        text_prompt(),
                        audio_letter_box()
                    ]
                )
            else:
                return build_response(
                    build_attr(qp, diag, NE, NW, SE, SW, "southeast statue"),
                    [
                        text_title_walk_southeast_statue(),
                        text_walk_to_southeast_statue(),
                        text_prompt()
                    ]
                )
        elif (obj == "southwest statue") or (obj == "southwest raven"):
            [lap_done, diag] = update_lap(diag, "A")
            if (lap_done):
                SaveQuestPoint(session, qp + 1)
                return build_response(
                    build_attr(qp + 1, diag, NE, NW, SE, SW, "southwest statue"),
                    [
                        text_title_walk_southwest_statue(),
                        text_walk_to_qp4_end_southwest_statue(),
                        text_prompt(),
                        audio_letter_box()
                    ]
                )
            else:
                return build_response(
                    build_attr(qp, diag, NE, NW, SE, SW, "southwest statue"),
                    [
                        text_title_walk_southwest_statue(),
                        text_walk_to_southwest_statue(),
                        text_prompt()
                    ]
                )
        else:
            return misunderstand_response(attr)
    else:
        if (obj == "northeast statue") or (obj == "northeast raven"):
            return build_response(
                build_attr(qp, diag, NE, NW, SE, SW, "northeast statue"),
                [
                    text_title_walk_northeast_statue(),
                    text_walk_to_northeast_statue(),
                    text_prompt()
                ]
            )
        elif (obj == "northwest statue") or (obj == "northwest raven"):
            return build_response(
                build_attr(qp, diag, NE, NW, SE, SW, "northwest statue"),
                [
                    text_title_walk_northwest_statue(),
                    text_walk_to_northwest_statue(),
                    text_prompt()
                ]
            )
        elif (obj == "southeast statue") or (obj == "southeast raven"):
            return build_response(
                build_attr(qp, diag, NE, NW, SE, SW, "southeast statue"),
                [
                    text_title_walk_southeast_statue(),
                    text_walk_to_southeast_statue(),
                    text_prompt()
                ]
            )
        elif (obj == "southwest statue") or (obj == "southwest raven"):
            return build_response(
                build_attr(qp, diag, NE, NW, SE, SW, "southwest statue"),
                [
                    text_title_walk_southwest_statue(),
                    text_walk_to_southwest_statue(),
                    text_prompt()
                ]
            )
        else:
            return misunderstand_response(attr)

def on_intent_walk(session, obj):
    qp = get_quest_point(session)
    diag = get_diag_order(session)
    NE = get_ne_complete(session)
    NW = get_nw_complete(session)
    SE = get_se_complete(session)
    SW = get_sw_complete(session)
    attr = session['attributes']

    if (obj == "north wall") or (obj == "north"):
        return build_response(
            build_attr(qp, diag, NE, NW, SE, SW, "north wall"),
            [
                text_title_walk_north_wall(),
                text_walk_to_north_wall(),
                text_prompt()
            ]
        )
    elif (obj == "south wall") or (obj == "south"):
        return build_response(
            build_attr(qp, diag, NE, NW, SE, SW, "south wall"),
            [
                text_title_walk_south_wall(),
                text_walk_to_south_wall(),
                text_prompt()
            ]
        )
    elif (obj == "east wall") or (obj == "east"):
        return build_response(
            build_attr(qp, diag, NE, NW, SE, SW, "east wall"),
            [
                text_title_walk_east_wall(),
                text_walk_to_east_wall(),
                text_prompt()
            ]
        )
    elif (obj == "west wall") or (obj == "west"):
        return build_response(
            build_attr(qp, diag, NE, NW, SE, SW, "west wall"),
            [
                text_title_walk_west_wall(),
                text_walk_to_west_wall(),
                text_prompt()
            ]
        )
    elif (obj == "wall"):
        return build_response(
            build_attr(qp, diag, NE, NW, SE, SW, get_context(session)),
            [
                text_wall_prompt(),
                text_walk_to_wall(),
                text_wall_prompt()
            ]
        )
    elif (obj == "letter"):
        return build_response(
            build_attr(qp, diag, NE, NW, SE, SW, "letter"),
            [
                text_title_walk_letter(),
                text_walk_to_letter_box(),
                text_prompt()
            ]
        )
    elif (obj == "letter box"):
        return build_response(
            build_attr(qp, diag, NE, NW, SE, SW, "letter box"),
            [
                text_title_walk_letter_box(),
                text_walk_to_letter_box(),
                text_prompt()
            ]
        )
    elif (obj == "metal cabinet" or (obj == "cabinet")):
        return build_response(
            build_attr(qp, diag, NE, NW, SE, SW, "metal cabinet"),
            [
                text_title_walk_metal_cabinet(),
                text_walk_to_metal_cabinet(),
                text_prompt()
            ]
        )
    elif ((obj == "northeast terminal") or  (obj == "northwest terminal") or
              (obj == "southeast terminal") or (obj == "southwest terminal") or
              (obj == "central terminal") or (obj == "terminal") or
              (obj == "northeast computer") or (obj == "northwest computer") or
              (obj == "southeast computer") or (obj == "southwest computer") or
              (obj == "central computer") or (obj == "computer") or
              (obj == "computer terminal")):
        return on_intent_walk_terminal(session, obj)
    elif ((obj == "northeast statue") or (obj == "northwest statue") or
          (obj == "southeast statue") or (obj == "southwest statue") or
          (obj == "northeast raven") or (obj == "northwest raven") or
          (obj == "southeast raven") or (obj == "southwest raven") or
          (obj == "statue") or (obj == "raven")):
        return on_intent_walk_statue(session, obj)
    elif ((obj == "northeast") or (obj == "northwest") or
          (obj == "southeast") or (obj == "southwest") or
          (obj == "northeast corner") or (obj == "northwest corner") or
          (obj == "southeast corner") or (obj == "southwest corner")):
        if qp < 6:
            return on_intent_walk_statue(session, obj + " statue")
        else:
            return on_intent_walk_terminal(session, obj + " terminal")
    else:
        return misunderstand_response(attr)

def on_intent_interact_with_terminal(session, obj):
    qp = get_quest_point(session)
    diag = get_diag_order(session)
    NE = get_ne_complete(session)
    NW = get_nw_complete(session)
    SE = get_se_complete(session)
    SW = get_sw_complete(session)
    attr = session['attributes']

    if qp == 0:
        SaveQuestPoint(session, qp + 1)
        return build_response(
            build_attr(qp + 1, diag, NE, NW, SE, SW, "central terminal"),
            [
                text_title_only_computer_terminal_qp0(),
                text_interact_only_computer_terminal_qp0(),
                text_prompt(),
                audio_letter_box()
            ]
        )
    elif qp < 6:
        return build_response(
            build_attr(qp, diag, NE, NW, SE, SW, "central terminal"),
            [
                text_title_computer_terminal_not_responding(),
                text_interact_only_computer_terminal(),
                text_prompt()
            ]
        )
    elif (obj == "northeast terminal")  or (obj == "northeast computer"):
        if ((qp == 6) and (get_ne_complete(session) == False)):
            return build_response(
                build_attr(qp, diag, NE, NW, SE, SW, "qp6_ne"),
                [
                    text_title_northeast_computer_terminal_qp6(),
                    text_interact_northeast_computer_terminal_qp6(),
                    text_options_prompt()
                ]
            )
        else:
            return build_response(
                build_attr(qp, diag, NE, NW, SE, SW, "northeast terminal"),
                [
                    text_title_computer_terminal_not_responding(),
                    text_interact_northeast_computer_terminal(),
                    text_prompt()
                ]
            )
    elif (obj == "northwest terminal") or (obj == "northwest computer"):
        if ((qp == 6) and (get_nw_complete(session) == False)):
            return build_response(
                build_attr(qp, diag, NE, NW, SE, SW, "qp6_nw"),
                [
                    text_title_northwest_computer_terminal_qp6(),
                    text_interact_northwest_computer_terminal_qp6(),
                    text_options_prompt()
                ]
            )
        else:
            return build_response(
                build_attr(qp, diag, NE, NW, SE, SW, "northwest terminal"),
                [
                    text_title_computer_terminal_not_responding(),
                    text_interact_northwest_computer_terminal(),
                    text_prompt()
                ]
            )
    elif (obj == "southeast terminal") or (obj == "southeast computer"):
        if ((qp == 6) and (get_se_complete(session) == False)):
            return build_response(
                build_attr(qp, diag, NE, NW, SE, SW, "qp6_se"),
                [
                    text_title_southeast_computer_terminal_qp6(),
                    text_interact_southeast_computer_terminal_qp6(),
                    text_options_prompt()
                ]
            )
        else:
            return build_response(
                build_attr(qp, diag, NE, NW, SE, SW, "southeast terminal"),
                [
                    text_title_computer_terminal_not_responding(),
                    text_interact_southeast_computer_terminal(),
                    text_prompt()
                ]
            )
    elif (obj == "southwest terminal") or (obj == "southwest computer"):
        if ((qp == 6) and (get_sw_complete(session) == False)):
            return build_response(
                build_attr(qp, diag, NE, NW, SE, SW, "qp6_sw"),
                [
                    text_title_southwest_computer_terminal_qp6(),
                    text_interact_southwest_computer_terminal_qp6(),
                    text_options_prompt()
                ]
            )
        else:
            return build_response(
                build_attr(qp, diag, NE, NW, SE, SW, "southwest terminal"),
                [
                    text_title_computer_terminal_not_responding(),
                    text_interact_southwest_computer_terminal(),
                    text_prompt()
                ]
            )
    elif (obj == "central terminal") or (obj == "central computer"):
        return build_response(
            build_attr(qp, diag, NE, NW, SE, SW, "central terminal"),
            [
                text_title_computer_terminal_not_responding(),
                text_interact_central_computer_terminal(),
                text_prompt()
            ]
        )
    elif (obj == "terminal") or (obj == "computer terminal") or (obj == "computer"):
        return build_response(
            build_attr(qp, diag, NE, NW, SE, SW, get_context(session)),
            [
                text_terminal_prompt(),
                text_interact_terminal(),
                text_terminal_prompt()
            ]
        )
    else:
        return misunderstand_response(attr)

def on_intent_interact_with_statue(session, obj):
    qp = get_quest_point(session)
    diag = get_diag_order(session)
    NE = get_ne_complete(session)
    NW = get_nw_complete(session)
    SE = get_se_complete(session)
    SW = get_sw_complete(session)
    attr = session['attributes']

    if qp >= 6:
        return misunderstand_response(attr)
    elif (obj == "northeast statue") or (obj == "northeast raven"):
        return build_response(
            build_attr(qp, diag, NE, NW, SE, SW, "northeast statue"),
            [
                text_title_interact_statue(),
                text_interact_northeast_statue(),
                text_prompt()
            ]
        )
    elif (obj == "northwest statue") or (obj == "northwest raven"):
        return build_response(
            build_attr(qp, diag, NE, NW, SE, SW, "northwest statue"),
            [
                text_title_interact_statue(),
                text_interact_northwest_statue(),
                text_prompt()
            ]
        )
    elif (obj == "southeast statue") or (obj == "southeast raven"):
        return build_response(
            build_attr(qp, diag, NE, NW, SE, SW, "southeast statue"),
            [
                text_title_interact_statue(),
                text_interact_southeast_statue(),
                text_prompt()
            ]
        )
    elif (obj == "southwest statue") or (obj == "southwest raven"):
        return build_response(
            build_attr(qp, diag, NE, NW, SE, SW, "southwest statue"),
            [
                text_title_interact_statue(),
                text_interact_southwest_statue(),
                text_prompt()
            ]
        )
    elif (obj == "statue") or (obj == "raven"):
        return build_response(
            build_attr(qp, diag, NE, NW, SE, SW, get_context(session)),
            [
                text_statue_prompt(),
                text_interact_statue(),
                text_statue_prompt()
            ]
        )
    else:
        return misunderstand_response(attr)


def on_intent_interact_with(session, obj):
    qp = get_quest_point(session)
    diag = get_diag_order(session)
    NE = get_ne_complete(session)
    NW = get_nw_complete(session)
    SE = get_se_complete(session)
    SW = get_sw_complete(session)
    attr = session['attributes']

    if (obj == "north wall") or (obj == "north"):
        if (qp == 2):
            SaveQuestPoint(session, qp + 1)
            return build_response(
                build_attr(qp + 1, diag, NE, NW, SE, SW, "north wall"),
                [
                    text_title_interact_north_wall(),
                    text_interact_north_wall_qp2(),
                    text_prompt(),
                    audio_moving_wall(),
                    audio_letter_box()
                ]
            )
        else:
            return build_response(
                build_attr(qp, diag, NE, NW, SE, SW, "north wall"),
                [
                    text_title_interact_north_wall_qp2(),
                    text_interact_north_wall(),
                    text_prompt()
                ]
            )
    elif (obj == "south wall") or (obj == "south"):
        return build_response(
            build_attr(qp, diag, NE, NW, SE, SW, "south wall"),
            [
                text_title_interact_south_wall(),
                text_interact_south_wall(),
                text_prompt()
            ]
        )
    elif (obj == "east wall") or (obj == "east"):
        return build_response(
            build_attr(qp, diag, NE, NW, SE, SW, "east wall"),
            [
                text_title_interact_east_wall(),
                text_interact_east_wall(),
                text_prompt()
            ]
        )
    elif (obj == "west wall") or (obj == "west"):
        return build_response(
            build_attr(qp, diag, NE, NW, SE, SW, "west wall"),
            [
                text_title_interact_west_wall(),
                text_interact_west_wall(),
                text_prompt()
            ]
        )
    elif (obj == "wall"):
        return build_response(
            build_attr(qp, diag, NE, NW, SE, SW, get_context(session)),
            [
                text_wall_prompt(),
                text_interact_wall(),
                text_wall_prompt()
            ]
        )
    elif (obj == "letter"):
        return on_intent_read(session)
    elif (obj == "letter box"):
        return build_response(
            build_attr(qp, diag, NE, NW, SE, SW, "letter box"),
            [
                text_title_interact_letter_box(),
                text_interact_letter_box(),
                text_prompt()
            ]
        )
    elif (obj == "metal cabinet") or (obj == "cabinet"):
        return build_response(
            build_attr(qp, diag, NE, NW, SE, SW, "metal cabinet"),
            [
                text_title_interact_metal_cabinet(),
                text_interact_metal_cabinet(),
                text_prompt()
            ]
        )
    elif ((obj == "northeast terminal") or  (obj == "northwest terminal") or
          (obj == "southeast terminal") or (obj == "southwest terminal") or
          (obj == "central terminal") or (obj == "terminal") or
          (obj == "northeast computer") or (obj == "northwest computer") or
          (obj == "southeast computer") or (obj == "southwest computer") or
          (obj == "central computer") or (obj == "computer") or
          (obj == "computer terminal")):
        if (obj == "terminal") or (obj == "computer") or (obj == "computer terminal"):
            context = get_context(session)
            if ("terminal" in context):
                obj = context
        return on_intent_interact_with_terminal(session, obj)
    elif ((obj == "northeast statue") or (obj == "northwest statue") or
          (obj == "southeast statue") or (obj == "southwest statue") or
          (obj == "northeast raven") or (obj == "northwest raven") or
          (obj == "southeast raven") or (obj == "southwest raven") or
          (obj == "statue") or (obj == "raven")):
        if (obj == "statue") or (obj == "raven"):
            context = get_context(session)
            if ("statue" in context):
                obj = context
        return on_intent_interact_with_statue(session, obj)
    elif ((obj == "northeast") or (obj == "northwest") or
          (obj == "southeast") or (obj == "southwest") or
          (obj == "northeast corner") or (obj == "northwest corner") or
          (obj == "southeast corner") or (obj == "southwest corner")):
        if qp < 6:
            return on_intent_interact_with_statue(session, obj + " statue")
        else:
            return on_intent_interact_with_terminal(session, obj + " terminal")
    else:
        return misunderstand_response(attr)

def on_intent_read(session):
    qp = get_quest_point(session)
    diag = get_diag_order(session)
    NE = get_ne_complete(session)
    NW = get_nw_complete(session)
    SE = get_se_complete(session)
    SW = get_sw_complete(session)
    context = get_context(session)
    attr = session['attributes']

    if (qp == 0):
        return misunderstand_response(attr)
    elif (qp == 1):
        SaveQuestPoint(session, 2)
        return build_response(
            build_attr(2, "", False, False, False, False, context),
            [
                text_title_read_letter(),
                text_interact_letter_qp2_first_time(),
                text_prompt(),
                audio_sharp_click()
            ]
        )
    elif (qp == 2):
        return build_response(
            build_attr(2, "", False, False, False, False, context),
            [
                text_title_read_letter(),
                text_interact_letter_qp2(),
                text_prompt()
            ]
        )
    elif (qp == 3):
        SaveQuestPoint(session, 4)
        return build_response(
            build_attr(4, "", False, False, False, False, context),
            [
                text_title_read_letter(),
                text_interact_letter_qp4(),
                text_prompt()
            ]
        )
    elif (qp == 4):
        return build_response(
            build_attr(4, diag, False, False, False, False, context),
            [
                text_title_read_letter(),
                text_interact_letter_qp4(),
                text_prompt()
            ]
        )
    elif (qp == 5):
        SaveQuestPoint(session, 6)
        return build_response(
            build_attr(6, "", False, False, False, False, context),
            [
                text_title_read_letter(),
                text_interact_letter_qp6_first_time(),
                text_prompt(),
                audio_moving_statue()
            ]
        )
    elif (qp == 6):
        return build_response(
            build_attr(6, "", NE, NW, SE, SW, context),
            [
                text_title_read_letter(),
                text_interact_letter_qp6(),
                text_prompt()
            ]
        )
    elif (qp == 7) or (qp == 8):
        if (qp == 7):
            SaveQuestPoint(session, 8)
        return build_response(
            build_attr(8, "", False, False, False, False, context),
            [
                text_title_read_letter(),
                text_interact_letter_qp8(),
                text_prompt()
            ]
        )
    elif (qp == 9):
        SaveQuestPoint(session, 0)
        return build_response(
            {},
            [
                text_title_read_letter(),
                text_end(),
                "",
                audio_jingle()
            ],
            True
        )
    else:
        return error_response()


def on_intent_option(session, intent):
    option = get_option_slot(intent)
    NE = get_ne_complete(session)
    NW = get_nw_complete(session)
    SE = get_se_complete(session)
    SW = get_sw_complete(session)
    context = get_context(session)
    attr = session['attributes']

    if (context == "qp6_ne"):
        if (option == "1"):
            return build_response(
                build_attr(6, "", NE, NW, SE, SW, "northeast terminal"),
                [
                    text_title_nice_option(),
                    text_option_non_end_northeast_computer_terminal_a(),
                    text_prompt()
                ]
            )
        elif (option == "2"):
            if NW and SE and SW:
                SaveQuestPoint(session, 7)
                return build_response(
                    build_attr(7, "", False, False, False, False, "northeast terminal"),
                    [
                        text_title_mean_option(),
                        text_option_end_northeast_computer_terminal_b(),
                        text_prompt(),
                        audio_computer_beeping(),
                        audio_letter_box()
                    ]
                )
            else:
                return build_response(
                    build_attr(6, "", True, NW, SE, SW, "northeast terminal"),
                    [
                        text_title_mean_option(),
                        text_option_non_end_northeast_computer_terminal_b(),
                        text_prompt()
                    ]
                )
        else:
            return misunderstand_response(attr)
    elif (context == "qp6_nw"):
        if (option == "1"):
            if NE and SE and SW:
                SaveQuestPoint(session, 7)
                return build_response(
                    build_attr(7, "", False, False, False, False, "northwest terminal"),
                    [
                        text_title_mean_option(),
                        text_option_end_northwest_computer_terminal_a(),
                        text_prompt(),
                        audio_computer_beeping(),
                        audio_letter_box()
                    ]
                )
            else:
                return build_response(
                    build_attr(6, "", NE, True, SE, SW, "northwest terminal"),
                    [
                        text_title_mean_option(),
                        text_option_non_end_northwest_computer_terminal_a(),
                        text_prompt()
                    ]
                )
        elif (option == "2"):
            return build_response(
                build_attr(6, "", NE, NW, SE, SW, "northwest terminal"),
                [
                    text_title_nice_option(),
                    text_option_non_end_northwest_computer_terminal_b(),
                    text_prompt()
                ]
            )
        else:
            return misunderstand_response(attr)
    elif (context == "qp6_se"):
        if (option == "1"):
            return build_response(
                build_attr(6, "", NE, NW, SE, SW, "southeast terminal"),
                [
                    text_title_nice_option(),
                    text_option_non_end_southeast_computer_terminal_a(),
                    text_prompt()
                ]
            )
        elif (option == "2"):
            if NE and NW and SW:
                SaveQuestPoint(session, 7)
                return build_response(
                    build_attr(7, "", False, False, False, False, "southeast terminal"),
                    [
                        text_title_mean_option(),
                        text_option_end_southeast_computer_terminal_b(),
                        text_prompt(),
                        audio_computer_beeping(),
                        audio_letter_box()
                    ]
                )
            else:
                return build_response(
                    build_attr(6, "", NE, NW, True, SW, "southeast terminal"),
                    [
                        text_title_mean_option(),
                        text_option_non_end_southeast_computer_terminal_b(),
                        text_prompt()
                    ]
                )
        else:
            return misunderstand_response(attr)
    elif (context == "qp6_sw"):
        if (option == "1"):
            if NE and NW and SE:
                SaveQuestPoint(session, 7)
                return build_response(
                    build_attr(7, "", False, False, False, False, "southwest terminal"),
                    [
                        text_title_mean_option(),
                        text_option_end_southwest_computer_terminal_a(),
                        text_prompt(),
                        audio_computer_beeping(),
                        audio_letter_box()
                    ]
                )
            else:
                return build_response(
                    build_attr(6, "", NE, NW, SE, True, "southwest terminal"),
                    [
                        text_title_mean_option(),
                        text_option_non_end_southwest_computer_terminal_a(),
                        text_prompt()
                    ]
                )
        elif (option == "2"):
            return build_response(
                build_attr(6, "", NE, NW, SE, SW, "southwest terminal"),
                [
                    text_title_nice_option(),
                    text_option_non_end_southwest_computer_terminal_b(),
                    text_prompt()
                ]
            )
        else:
            return misunderstand_response(attr)
    else:
        return error_response()




# --------------- Events ------------------


def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    return on_intent_start(session)


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    if (get_is_playing(session) == False):
        return on_intent_start(session)
    elif (intent_name == "AMAZON.StartOverIntent"):
        SaveQuestPoint(session, 0)
        return on_intent_startover()
    elif (intent_name == "AMAZON.StopIntent") or (intent_name == "AMAZON.CancelIntent"):
        return on_intent_stop()
    elif (intent_name == "PlayIntent"):
        return on_intent_start(session)
    elif ("qp6_" in get_context(session)):
        if (intent_name == "OptionIntent"):
            return on_intent_option(session, intent)
        elif (intent_name == "AMAZON.HelpIntent"):
            return on_intent_help_on_terminal(session)
        elif (intent_name == "AMAZON.RepeatIntent"):
            return on_intent_repeat_on_terminal(session)
        else:
            return misunderstand_response(session['attributes'])
    elif (intent_name == "AMAZON.HelpIntent"):
        return on_intent_help(session)
    elif (intent_name == "AMAZON.RepeatIntent"):
        return on_intent_repeat(session)
    elif (intent_name == "WalkIntent"):
        return on_intent_walk(session, get_object_slot(intent))
    elif (intent_name == "InteractIntent"):
        return on_intent_interact_with(session, get_context(session))
    elif (intent_name == "InteractWithIntent"):
        return on_intent_interact_with(session, get_object_slot(intent))
    elif (intent_name == "ReadIntent"):
        return on_intent_read(session)
    elif (intent_name == "OptionIntent"):
        return misunderstand_response(session['attributes'])
    else:
        return error_response()


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    if (event['session']['application']['applicationId'] !=
             "amzn1.ask.skill.a378ad35-70d7-4bda-a6ae-adc144158b0f"):
         raise ValueError("Invalid Application ID")

    global locale
    locale = event['request']['locale']
    print("locale is " + locale)

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])