#Outsiders Final Project Game - Full Pygame Version
import math
import pygame
import sys
 
pygame.init()
 
# ── Screen & fonts ──────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1200, 800
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("THE OUTSIDERS: VIDEO GAME")
 
try:
    title_font  = pygame.font.Font('GAMEFONT.ttf', 50)
    game_font   = pygame.font.Font('GAMEFONT.ttf', 26)
    small_font  = pygame.font.Font('GAMEFONT.ttf', 20)
    choice_font = pygame.font.Font('GAMEFONT.ttf', 22)
except FileNotFoundError:
    title_font  = pygame.font.SysFont('courier', 50, bold=True)
    game_font   = pygame.font.SysFont('courier', 26)
    small_font  = pygame.font.SysFont('courier', 20)
    choice_font = pygame.font.SysFont('courier', 22)
 
clock = pygame.time.Clock()
 
# ── Colors ───────────────────────────────────────────────────────────────────
BLACK      = (0,   0,   0)
WHITE      = (255, 255, 255)
GOLD       = (212, 175, 55)
DIM_GOLD   = (140, 110, 30)
RED        = (180, 40,  40)
DARK_RED   = (100, 20,  20)
DARK_GRAY  = (20,  20,  20)
MID_GRAY   = (50,  50,  50)
LIGHT_GRAY = (180, 180, 180)
 
# ── Layout constants ──────────────────────────────────────────────────────────
BAR_H      = 90          # top/bottom black bars
TEXT_Y     = BAR_H + 12  # where scrollable text starts
CHOICE_Y   = SCREEN_H - BAR_H - 130  # top of choice buttons area
TEXT_H     = CHOICE_Y - TEXT_Y - 8   # height of text viewport
 
CHOICE_BTN_H   = 44
CHOICE_BTN_GAP = 10
MAX_CHOICES    = 4
 
#Background
try:
    background = pygame.image.load('TITLE.png').convert()
    background = pygame.transform.scale(background, (SCREEN_W, SCREEN_H))
except FileNotFoundError:
    background = pygame.Surface((SCREEN_W, SCREEN_H))
    background.fill((15, 10, 5))
 
#Overlay (darkens background in game mode)
overlay = pygame.Surface((SCREEN_W, SCREEN_H))
overlay.set_alpha(170)
overlay.fill(BLACK)
 

#TEXT WRAPPING HELPER
def wrap_text(text, font, max_width):
    """Return list of rendered lines (surfaces, rects not yet set)."""
    lines = []
    for paragraph in text.split('\n'):
        paragraph = paragraph.strip()
        if paragraph == '':
            lines.append(None)   # blank spacer
            continue
        words = paragraph.split(' ')
        current = ''
        for word in words:
            test = (current + ' ' + word).strip()
            if font.size(test)[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
    return lines
 
 
#GAME STATE
class GameState:
    TITLE      = 'title'
    FADE_IN    = 'fade_in'
    NARRATIVE  = 'narrative'    # showing text, waiting for SPACE / click
    CHOICE     = 'choice'       # showing choices
    GAME_OVER  = 'game_over'
    WIN        = 'win'
    FADE_LEVEL = 'fade_level'   # short fade between levels
 
state        = GameState.TITLE
fade_alpha   = 0
fade_speed   = 6
 
current_level   = 0   # 0 = title; 1-7 = levels
pending_level   = 1
 
#Scroll variables
scroll_y        = 0
scroll_target   = 0
LINE_H          = 32
 
#text lines currently rendered
text_lines      = []
text_color      = WHITE
 
#choice state
choices         = []          # list of dicts {label, next_fn}
hovered_choice  = -1

LEVELS = {}   # filled below
 
def make_node(t, **kw):
    return {'type': t, **kw}

#LEVEL DATA
 
LEVELS[1] = {
    'title': 'LEVEL 1: EAST SIDE STREETS',
    'start': 'intro',
    'nodes': {
        'intro': make_node('text',
            text=(
                "LEVEL 1: EAST SIDE STREETS\n\n"
                "You're Ponyboy Curtis. Fourteen years old, greaser.\n"
                "You just walked out of a Paul Newman picture alone,\n"
                "and you already know that was a mistake.\n\n"
                "The streets of the East Side stretch out ahead of you.\n"
                "Your neighborhood. Your turf. But alone, it's dangerous.\n\n"
                "Which way do you go home?"
            ),
            next='choice_route'),
 
        'choice_route': make_node('choice',
            options=[
                ("Back alleys",            'alley'),
                ("Main street",            'main'),
                ("Cut through Soc territory", 'soc_territory'),
            ]),
 
        'soc_territory': make_node('gameover',
            text=(
                "You figure it'll be faster. It isn't.\n\n"
                "A pack of Socs spots you two blocks in, and you're totally alone, "
                "deep in their turf. No one's coming to save you.\n"
                "They beat you bad enough that you wake up in the gutter.\n"
                "Darry has to tell the judge. This might be the end of the three of you.\n\n"
                "You walked into Soc territory alone.\nThat might as well have been death wish."
            ),
            retry_level=1),
 
        'alley': make_node('text',
            text=(
                "Smart. But not smart enough.\n\n"
                "A blue Mustang rolls up slow behind you. Socs.\n\n"
                "Five of them pile out. They grab you, shove you against a fence.\n"
                "'Greaser scum,' one of them spits.\n\n"
                "Do you..."
            ),
            next='choice_fight'),
 
        'main': make_node('text',
            text=(
                "You try to stay visible. Doesn't help.\n\n"
                "A blue Mustang cuts you off at the corner. Socs.\n\n"
                "Five of them pile out. They grab you, shove you against a fence.\n"
                "'Greaser scum,' one of them spits.\n\n"
                "Do you..."
            ),
            next='choice_fight'),
 
        'choice_fight': make_node('choice',
            options=[
                ("Yell for help",          'yell'),
                ("Fight back",             'fight'),
                ("Stay quiet and take it", 'quiet'),
            ]),
 
        'quiet': make_node('gameover',
            text=(
                "You go limp and say nothing. They take that as an invitation.\n"
                "By the time they're done, you can barely stand.\n"
                "No one heard, nor came. You lay there until morning.\n\n"
                "You chose to stay silent. In this town, silence doesn't\n"
                "protect you, it just means no one knows to find you."
            ),
            retry_level=1),
 
        'yell': make_node('text',
            text="You yell out, hearing your voice echoes off the buildings.",
            next='rescue'),
 
        'fight': make_node('text',
            text="You throw a desparate punch. It barely connects, but it bought you a second.",
            next='rescue'),
 
        'rescue': make_node('text',
            text=(
                "Then you hear it, boots on pavement.\n"
                "You see your gang; Darry, Soda, Dally, Johnny, Two-Bit.\n"
                "The Socs back off and peel out.\n\n"
                "Soda throws an arm around you.\n"
                "'Don't walk alone, Pony. You know better than to act like a dingus.'\n\n"
                "You know, you just forget sometimes that the world isn't safe.\n\n"
                ">>> Level 1 complete."
            ),
            next='__next_level__'),
    }
}
 

LEVELS[2] = {
    'title': 'LEVEL 2: THE DRIVE-IN',
    'start': 'intro',
    'nodes': {
        'intro': make_node('text',
            text=(
                "LEVEL 2: THE DRIVE-IN\n\n"
                "Its Friday night. You, Johnny, and Dally sneak into the Nightly Double.\n"
                "No money for tickets. Never have money for tickets.\n\n"
                "You find seats behind two girls.\n"
                "Madras shirts, nice hair, Soc girls, and way out of your league.\n"
                "Dally starts running his mouth at them immediately.\n\n"
                "Do you..."
            ),
            next='choice_dally'),
 
        'choice_dally': make_node('choice',
            options=[
                ("Let Dally do his thing",       'dally_loose'),
                ("Tell him to lay off",          'dally_cool'),
                ("Leave before trouble starts",  'leave'),
            ]),
 
        'leave': make_node('gameover',
            text=(
                "You grab Johnny and start to head out.\n"
                "Dally doesn't follow. An hour later you hear he started a fight\n"
                "with the girls' boyfriends — Bob and Randy.\n"
                "Bob pulls a blade. Dally ends up in the hospital.\n"
                "You never meet Cherry Valance. The rumble has no informant.\n"
                "Everything that follows goes worse. Much worse.\n\n"
                "You walked away from the drive-in. Sometimes the people\nyou meet by accident are the ones who matter most."
            ),
            retry_level=2),
 
        'dally_loose': make_node('text',
            text=(
                "The girls look uncomfortable. One of them, Cherry Valance, turns around and throws her Coke in Dally's face.\n"
                "'Take a walk,' she says.\n\n"
                "Dally walks off in a huff, and you end up sitting next to Cherry.\n"
                "She's different from what you expected.\n"
                "She talks to you like a person.\n\n"
                "'You know,' she says, 'things are rough all over.'\n\n"
                "What do you talk about?"
            ),
            next='choice_talk'),
 
        'dally_cool': make_node('text',
            text=(
                "Johnny quietly tells Dally to cool it, and to your surprise, he listens.\n"
                "Cherry Valance turns around and smiles at Johnny.\n"
                "'Thanks,' she says.\n\n"
                "Dally walks off in a huff, and you end up sitting next to Cherry.\n"
                "She's different from what you expected.\n"
                "She talks to you like a person.\n\n"
                "'You know,' she says, 'things are rough all over.'\n\n"
                "What do you talk about?"
            ),
            next='choice_talk'),
 
        'choice_talk': make_node('choice',
            options=[
                ("Movies",                          'movies'),
                ("The gang divide",                 'divide'),
                ("Pick a fight about Socs",         'fight_cherry'),
            ]),
 
        'fight_cherry': make_node('gameover',
            text=(
                "You say something sharp about rich kids who never face consequences.\n"
                "Cherry's expression closes like a door.\n"
                "'You don't know anything about my life,' she says, and moves away.\n\n"
                "You never get close enough to Cherry to matter.\n"
                "When the park happens, there is no one on the inside to help.\n\n"
                "You pushed Cherry away.\nShe could have saved you, but instead you chose to drown in your pride."
            ),
            retry_level=2),
 
        'movies': make_node('text',
            text=(
                "You bond over Paul Newman. She laughs at your impression of him.\n"
                "For a minute, you forget she's a Soc.\n\n"
                "The night ends with her boyfriend Bob showing up, drunk and angry.\n"
                "She leaves with him, but something shifted tonight.\n\n"
                ">>> Level 2 complete."
            ),
            next='__next_level__'),
 
        'divide': make_node('text',
            text=(
                "She explains that Socs have their own kind of emptiness.\n"
                "Too much, too fast, too young.\n"
                "You've never thought about it that way.\n\n"
                "The night ends with her boyfriend Bob showing up, drunk and angry.\n"
                "She leaves with him. but something shifted tonight.\n\n"
                ">>> Level 2 complete."
            ),
            next='__next_level__'),
    }
}
 
LEVELS[3] = {
    'title': 'LEVEL 3: THE PARK',
    'start': 'intro',
    'nodes': {
        'intro': make_node('text',
            text=(
                "LEVEL 3: THE PARK\n\n"
                "You fell asleep in the lot with Johnny and got home past curfew.\n"
                "Darry slapped you for the first time. It hit harder than any Soc ever could.\n\n"
                "You ran, with Johnny running with you.\n"
                "Now it's 2 AM and you're both in the park, by the fountain.\n\n"
                "Then you see headlights, a blue Mustang, five figures.\n"
                "Bob, Randy, and three other Socs, all of them drunk.\n\n"
                "'Hey greasers, you been talking to our girls.'\n\n"
                "What do you do?"
            ),
            next='choice_park'),
 
        'choice_park': make_node('choice',
            options=[
                ("Stand your ground", 'stand'),
                ("Try to run",        'run'),
            ]),
 
        'run': make_node('text',
            text=(
                "No use, they're faster and there are more of them.\n"
                "They grab you and shove your head under the fountain water."
            ),
            next='drowning'),
 
        'stand': make_node('text',
            text=(
                "You don't back down, they don't like that.\n"
                "Bob grabs you and forces your face under the fountain."
            ),
            next='drowning'),
 
        'drowning': make_node('text',
            text=(
                "The water fills your nose, your throat, suffocating your mind and your lungs.\n"
                "You're drowning in a park fountain. You're actually drowning.\n\n"
                "Then you see a flash, hear a cry, and feel the hands let go.\n\n"
                "You pull yourself up, gasping. Johnny is standing there.\n"
                "His switchblade is in his hand. Bob is on the ground.\n"
                "Bob is not moving.\n\n"
                "Johnny looks at you. His face is white.\n"
                "'I killed him,' he says. 'Pony, I killed that boy.'\n\n"
                "What do you say?"
            ),
            next='choice_johnny'),
 
        'choice_johnny': make_node('choice',
            options=[
                ("We have to call the police",     'police'),
                ("We need to run",                 'run2'),
                ("Tell Johnny to turn himself in", 'abandon'),
            ]),
 
        'abandon': make_node('gameover',
            text=(
                "You panic., telling Johnny it was his knife, his call.\n"
                "You say you'll back up whatever story he tells, but alone.\n"
                "Johnny looks at you like you're a stranger.\n"
                "He turns himself in without you.\n\n"
                "The judge sends him to a boys' home.\n"
                "Darry yells at you for abandoning Johnny, and you're ostracized from the greasers.\n"
                "Eventually, someone rats your situation out, and you get split from Darry and Soda.\n\n"
                "You left Johnny to face it alone.\nGreasers don't do that to each other."
            ),
            retry_level=3),
 
        'police': make_node('text',
            text=(
                "Johnny shakes his head.\n"
                "'They would split us up, send you away from Darry.'\n"
                "He's right, and you both know it.\n"
                "Running is the only option."
            ),
            next='dally_plan'),
 
        'run2': make_node('text',
            text="Johnny nods, and you oth already know what has to happen next.",
            next='dally_plan'),
 
        'dally_plan': make_node('text',
            text=(
                "You go to Dally for he's the only one who'd know what to do.\n\n"
                ">>> Level 3 complete."
            ),
            next='__next_level__'),
    }
}
 

LEVELS[4] = {
    'title': 'LEVEL 4: WINDRIXVILLE CHURCH',
    'start': 'intro',
    'nodes': {
        'intro': make_node('text',
            text=(
                "LEVEL 4: WINDRIXVILLE CHURCH\n\n"
                "Dally gave you fifty bucks, a gun, and directions.\n"
                "Jay Mountain. An abandoned church. Lay low.\n\n"
                "You and Johnny hopped a freight train in the dark.\n"
                "You arrive at the church, smelling like old wood and dust.\n"
                "It's been empty for years, but now it's yours.\n\n"
                "Days pass, you eat bologna sandwiches and drink warm Pepsi.\n"
                "You play poker with matchsticks. You sleep on the hard floor.\n\n"
                "How do you pass the time?"
            ),
            next='choice_time'),
 
        'choice_time': make_node('choice',
            options=[
                ("Read",                             'read'),
                ("Watch from the window",            'watch'),
                ("Sneak into town for supplies",     'sneak'),
            ]),
 
        'sneak': make_node('gameover',
            text=(
                "You figure it's been five days — no one's looking anymore.\n"
                "You're wrong. A deputy in town recognizes you from the paper.\n"
                "You run, but he radios ahead.\n"
                "They pick up Johnny at the church.\n\n"
                "The trial is fast. The outcome isn't good.\n\n"
                "You broke cover too soon.\nPatience isn't your strong suit — but it had to be."
            ),
            retry_level=4),
 
        'read': make_node('text',
            text=(
                "You pick up Gone with the Wind from the stack Dally left.\n"
                "Johnny gets into it more than you expected.\n"
                "'The Southern gentlemen remind me of Socs,' he says.\n"
                "You read to him out loud when his eyes get tired."
            ),
            next='frost'),
 
        'watch': make_node('text',
            text=(
                "The valley below is quiet, littered with farms, roads, kids walking to school.\n"
                "You watch them and feel something you can't quite put your finger on.\n"
                "Is it longing, or maybe just distance."
            ),
            next='frost'),
 
        'frost': make_node('text',
            text=(
                "One morning you recite a Robert Frost poem to Johnny.\n"
                "'Nothing gold can stay,' you tell him.\n\n"
                "'What does that mean?' he asks.\n\n"
                "You think about it. 'That the good stuff goes fast, I guess.'\n\n"
                "Johnny stares at the sunrise. 'Yeah,' he says quietly.\n\n"
                "Five days in, Dally shows up with a letter from Sodapop.\n"
                "And news: a full rumble is being organized.\n"
                "Cherry is helping your side.\n\n"
                "Then you smell it. Smoke.\n"
                "The church is on fire.\n\n"
                ">>> Level 4 complete."
            ),
            next='__next_level__'),
    }
}
 
LEVELS[5] = {
    'title': 'LEVEL 5: THE FIRE',
    'start': 'intro',
    'nodes': {
        'intro': make_node('text',
            text=(
                "LEVEL 5: THE FIRE\n\n"
                "Flames are eating through the old church roof.\n"
                "A group of schoolkids on a field trip are screaming nearby.\n"
                "Their teacher is panicking. Some of the kids went inside.\n\n"
                "Johnny grabs your arm, his eyes are wild.\n"
                "'We started this,' he says. 'We have to get them out.'\n\n"
                "What do you do?"
            ),
            next='choice_fire'),
 
        'choice_fire': make_node('choice',
            options=[
                ("Go in after the kids",               'go_in'),
                ("Wait for the fire department",       'wait'),
                ("Run — you're already wanted",        'run'),
            ]),
 
        'run': make_node('gameover',
            text=(
                "You grab Johnny's sleeve and pull him toward the tree line.\n"
                "You can hear the kids screaming behind you. You run anyway.\n"
                "Two children don't make it out.\n\n"
                "When they find you, it isn't as a fugitive anymore.\n"
                "It's as something worse.\n\n"
                "You'll carry those kids' screams\nfor the rest of your life."
            ),
            retry_level=5),
 
        'wait': make_node('text',
            text=(
                "You hesitate for a second.\n"
                "Then you hear a child scream inside.\n"
                "You and Johnny run in anyway."
            ),
            next='inside'),
 
        'go_in': make_node('text',
            text="With No hesitation, both you and Johnny run straight through the front door.",
            next='inside'),
 
        'inside': make_node('text',
            text=(
                "Inside it's smoke and heat and orange light everywhere.\n"
                "You find the kids huddled in the corner, coughing.\n\n"
                "You start lifting them out through the window one by one.\n"
                "Three kids. Four. Five.\n\n"
                "Then the roof groans.\n\n"
                "Johnny is still inside. Do you..."
            ),
            next='choice_johnny'),
 
        'choice_johnny': make_node('choice',
            options=[
                ("Go back for him",                'go_back'),
                ("Yell for him to jump",           'yell'),
                ("Assume he found another way out",'assume'),
            ]),
 
        'assume': make_node('gameover',
            text=(
                "You figure he's smart enough to find the door.\n"
                "He wasn't, and the beam came down while he was still looking for you.\n"
                "Dally gets him out, but the damage is worse than it had to be.\n"
                "Johnny never wakes up.\n\n"
                "You overestimated, and now Johnny is dead"
            ),
            retry_level=5),
 
        'go_back': make_node('text',
            text=(
                "You turn back.\n"
                "Dally grabs you from behind and hauls you out.\n"
                "'Johnny is coming,' Dally growls."
            ),
            next='beam'),
 
        'yell': make_node('text',
            text=(
                "'JOHNNY! JUMP!'\n"
                "He appears at the window and he starts to come through."
            ),
            next='beam'),
 
        'beam': make_node('text',
            text=(
                "A burning beam comes down.\n"
                "It catches Johnny full across the back.\n\n"
                "Dally drags him out. You're both pulled back.\n"
                "The church collapses behind you.\n\n"
                "Johnny is alive, but his back is broken. He's badly burned and crippled.\n"
                "An ambulance is coming, and so are reporters.\n\n"
                "You're a hero. It doesn't feel like anything.\n\n"
                "At the hospital, Darry is waiting. He hugs you so hard it hurts.\n"
                "You finally understand — he was never angry. He was scared.\n\n"
                ">>> Level 5 complete."
            ),
            next='__next_level__'),
    }
}
 

LEVELS[6] = {
    'title': 'LEVEL 6: THE RUMBLE',
    'start': 'intro',
    'nodes': {
        'intro': make_node('text',
            text=(
                "LEVEL 6: THE RUMBLE\n\n"
                "The night of the rumble. Vacant lot, East Side.\n"
                "Twenty greasers. Twenty Socs. No weapons, just fists.\n\n"
                "Johnny is in the hospital in a critical condition.\n"
                "Dally checked himself out against doctor's orders to be here.\n"
                "His arm is in a sling but his eyes are fire.\n\n"
                "'We are doing this for Johnny,' Dally says.\n\n"
                "Before the fight, do you..."
            ),
            next='choice_psych'),
 
        'choice_psych': make_node('choice',
            options=[
                ("Psych yourself up",       'psych'),
                ("Think about Johnny",      'think'),
            ]),
 
        'psych': make_node('text',
            text=(
                "You roll your shoulders and crack your knuckles.\n"
                "You're small but you're fast. You've done this before."
            ),
            next='fight_starts'),
 
        'think': make_node('text',
            text=(
                "You think about Johnny in that hospital bed.\n"
                "The bandages. The machines.\n"
                "You fight harder because of it."
            ),
            next='fight_starts'),
 
        'fight_starts': make_node('text',
            text=(
                "The Socs' leader steps forward.\n"
                "Darry challenges all of the Socs, and a guy named Paul steps up.\n"
                "One punch from Paul lands before everything explodes.\n\n"
                "Fists and boots and shouting everywhere.\n"
                "You take a hit to the jaw, another to the ribs.\n\n"
                "A Soc pulls a blade, breaking the no-weapons rule."
            ),
            next='choice_blade'),
 
        'choice_blade': make_node('choice',
            options=[
                ("Call it out loud",           'call_out'),
                ("Dodge and keep fighting",    'dodge'),
                ("Grab the blade yourself",    'grab_blade'),
            ]),
 
        'grab_blade': make_node('gameover',
            text=(
                "You lunge for it. Your hand closes around the blade.\n"
                "It opens your palm to the bone, blood pours out.\n"
                "You go down, and when Socs see the blood, things escalate fast.\n"
                "Someone pulls a chain, and two greasers end up in the hospital.\n"
                "You never make it to Johnny in time.\n\n"
                "You grabbed a blade with your bare hand.\nBrave, but also stupid."
            ),
            retry_level=6),
 
        'call_out': make_node('text',
            text=(
                "'HE'S GOT A BLADE!' you shout.\n"
                "The crowd freezes, and the Soc tosses it, embarrassed.\n"
                "Fair fight restored."
            ),
            next='greasers_win'),
 
        'dodge': make_node('text',
            text=(
                "You sidestep it and catch him with a right hook.\n"
                "He goes down and you keep moving."
            ),
            next='greasers_win'),
 
        'greasers_win': make_node('text',
            text=(
                "Then the Socs break. They're running.\n"
                "The greasers won.\n\n"
                "No one cheers. Everyone is just breathing hard, bleeding.\n"
                "Dally is already pulling at your sleeve.\n"
                "'Hospital. Now. Johnny is asking for you.'\n\n"
                "You run.\n\n"
                "You're too late.\n\n"
                "Johnny looks at you. He barely manages three words:\n\n"
                "'Stay gold, Ponyboy.'\n\n"
                "Then, he's gone.\n\n"
                ">>> Level 6 complete."
            ),
            next='__next_level__'),
    }
}
 

LEVELS[7] = {
    'title': 'LEVEL 7: AFTERMATH',
    'start': 'intro',
    'nodes': {
        'intro': make_node('text',
            text=(
                "LEVEL 7: AFTERMATH\n\n"
                "Dally called from a payphone. He robbed a store.\n"
                "He wanted you all to know. He wanted you all to come.\n\n"
                "You ran to the vacant lot. Police were already there.\n"
                "Dally raised his unloaded gun.\n\n"
                "You knew what he was doing. You all did.\n"
                "He didn't want to live in a world without Johnny.\n\n"
                "The shots were quick. Dally dropped.\n\n"
                "Two in one night. You passed out on the pavement.\n\n"
                "Weeks go by in a fog.\n"
                "You failed English. You barely eat. You pick fights.\n"
                "Darry and Soda tiptoe around you.\n\n"
                "One night Soda runs out of the house crying. Do you..."
            ),
            next='choice_soda'),
 
        'choice_soda': make_node('choice',
            options=[
                ("Go after him",                  'chase'),
                ("Let him go",                    'darry_chase'),
                ("Tell Darry it's his problem",   'abandon_soda'),
            ]),
 
        'abandon_soda': make_node('gameover',
            text=(
                "Darry looks at you for a long moment.\n"
                "'He's your brother, Pony.'\n"
                "You shrug and go to your room.\n"
                "Soda doesn't come back that night. Or the next.\n"
                "The judge gets word the family is fracturing.\n"
                "You and Darry end up in separate placements.\n\n"
                "You let your family fall apart. After everything, that's the thing that finally breaks you."
            ),
            retry_level=7),
 
        'chase': make_node('text',
            text=(
                "You and Darry chase him down the street.\n"
                "The three of you stop under a streetlight, out of breath."
            ),
            next='soda_speaks'),
 
        'darry_chase': make_node('text',
            text=(
                "Darry grabs your arm. 'We go after him. Together.'\n"
                "You run."
            ),
            next='soda_speaks'),
 
        'soda_speaks': make_node('text',
            text=(
                "Soda turns around. His face is wrecked.\n"
                "'You two are always fighting and I am always in the middle\nand I cannot take it.'\n\n"
                "Something breaks open in you.\n"
                "You and Darry both start talking at once. Then stop. Then listen.\n\n"
                "For the first time in weeks, the three of you are just brothers.\n\n"
                "───\n\n"
                "Your English teacher offers you a deal:\n"
                "write one honest essay, pass the class.\n\n"
                "You find a note tucked inside your copy of Gone with the Wind.\n"
                "Johnny's handwriting. Shaky, but clear.\n\n"
                "'I have been thinking about what you said about staying gold.'\n"
                "'I think you still can. I think you should tell people.'\n"
                "'Not just greasers. Everyone.\nTell them it does not have to be like this.'\n\n"
                "Your essay is due tomorrow. Do you..."
            ),
            next='choice_essay'),
 
        'choice_essay': make_node('choice',
            options=[
                ("Write the whole truth",           'write_truth'),
                ("Skip it — you're done trying",    'skip'),
                ("Write it, but leave out Johnny",  'hollow'),
            ]),
 
        'skip': make_node('gameover',
            text=(
                "You stare at the blank page until midnight.\n"
                "Then you close the notebook.\n"
                "You fail English. The judge sees the report.\n"
                "You get placed in a home across town.\n"
                "Darry can't afford to fight it.\n"
                "Johnny's note sits unread in the back of the book.\n\n"
                "You gave up at the finish line.\nYou failed Johnny when you were almost there."
            ),
            retry_level=7),
 
        'hollow': make_node('text',
            text=(
                "You write around Johnny. Around Dally. Around all of it.\n"
                "It comes out hollow.\n"
                "Your teacher reads it and calls you in.\n"
                "'This isn't you, Ponyboy. I know you have more than this.'\n"
                "She gives you one more day.\n\n"
                "Do you..."
            ),
            next='choice_essay2'),
 
        'choice_essay2': make_node('choice',
            options=[
                ("Write the real version this time",  'write_truth'),
                ("Turn in the same hollow essay",     'skip'),
            ]),
 
        'write_truth': make_node('text',
            text=(
                "You start at the beginning.\n"
                "Or the middle. It all runs together.\n\n"
                "You write:\n\n"
                "   'When I stepped out into the bright sunlight\n"
                "    from the darkness of the movie house,\n"
                "    I had only two things on my mind.'\n\n"
                "You write all night. You write everything.\n"
                "You write it for Johnny. You write it for Dally.\n"
                "You write it so someone might understand.\n\n"
                "                    THE END\n\n"
                "              Stay Gold, Ponyboy."
            ),
            next='__win__'),
    }
}
 
#Navigation variables
nav_level    = 1      #current level number
nav_node_id  = None   #current node id within level
current_node = None   #resolved node dict
 
def load_node(level_num, node_id):
    global nav_level, nav_node_id, current_node
    global text_lines, scroll_y, scroll_target, state, choices, hovered_choice
    nav_level   = level_num
    nav_node_id = node_id
    current_node = LEVELS[level_num]['nodes'][node_id]
 
    ntype = current_node['type']
 
    if ntype == 'text':
        text_lines = wrap_text(current_node['text'], game_font, SCREEN_W - 80)
        scroll_y = scroll_target = 0
        state = GameState.NARRATIVE
        choices = []
 
    elif ntype == 'choice':
        choices = [{'label': label, 'next': nxt}
                   for label, nxt in current_node['options']]
        hovered_choice = -1
        state = GameState.CHOICE
 
    elif ntype == 'gameover':
        text_lines = wrap_text(
            current_node['text'] + '\n\nPress SPACE to retry or ESC to quit.',
            game_font, SCREEN_W - 80)
        scroll_y = scroll_target = 0
        state = GameState.GAME_OVER
 
    elif ntype == '__next_level__':   
        advance_level()
 
    elif ntype == '__win__':
        advance_win()
 
def advance_node():
    """Follow 'next' link from a text node."""
    nxt = current_node.get('next', None)
    if nxt == '__next_level__':
        advance_level()
    elif nxt == '__win__':
        advance_win()
    elif nxt:
        load_node(nav_level, nxt)
 
def choose_option(idx):
    """Select a choice."""
    ch = choices[idx]
    nxt = ch['next']
    if nxt == '__next_level__':
        advance_level()
    elif nxt == '__win__':
        advance_win()
    else:
        load_node(nav_level, nxt)
 
def advance_level():
    global state, pending_level, fade_alpha
    if nav_level >= 7:
        advance_win()
        return
    pending_level = nav_level + 1
    state = GameState.FADE_LEVEL
    fade_alpha = 0
 
def advance_win():
    global state, text_lines, scroll_y, scroll_target
    text_lines = wrap_text(
        "CONGRATULATIONS\n\n"
        "You made it through all seven levels.\n\n"
        "Stay gold.\n\n"
        "Press ESC to quit.",
        title_font, SCREEN_W - 80)
    scroll_y = scroll_target = 0
    state = GameState.WIN
 
def start_level(n):
    global state
    load_node(n, LEVELS[n]['start'])
 
#Draws all game assets
 
def draw_background(dim=True):
    screen.blit(background, (0, 0))
    if dim:
        screen.blit(overlay, (0, 0))
 
def draw_bars():
    pygame.draw.rect(screen, BLACK, (0, 0, SCREEN_W, BAR_H))
    pygame.draw.rect(screen, BLACK, (0, SCREEN_H - BAR_H, SCREEN_W, BAR_H))
    # gold border lines
    pygame.draw.line(screen, GOLD, (0, BAR_H), (SCREEN_W, BAR_H), 2)
    pygame.draw.line(screen, GOLD, (0, SCREEN_H - BAR_H), (SCREEN_W, SCREEN_H - BAR_H), 2)
 
def draw_title_header(text):
    surf = title_font.render(text, True, GOLD)
    screen.blit(surf, surf.get_rect(center=(SCREEN_W // 2, BAR_H // 2)))
 
def draw_bottom_hint(text):
    surf = small_font.render(text, True, DIM_GOLD)
    screen.blit(surf, surf.get_rect(center=(SCREEN_W // 2, SCREEN_H - BAR_H // 2)))
 
def draw_text_area():
    """Draw the scrollable text lines."""
    global scroll_y
    scroll_y += (scroll_target - scroll_y) * 0.18
 
    clip_rect = pygame.Rect(40, TEXT_Y, SCREEN_W - 80, TEXT_H)
    screen.set_clip(clip_rect)
 
    y = TEXT_Y - int(scroll_y)
    for line in text_lines:
        if line is None:
            y += LINE_H // 2
        else:
            surf = game_font.render(line, True, WHITE)
            screen.blit(surf, (40, y))
            y += LINE_H
 
    screen.set_clip(None)
 
    #scroll indicator
    total_h = sum(LINE_H if l else LINE_H // 2 for l in text_lines)
    if total_h > TEXT_H:
        ratio    = TEXT_H / total_h
        bar_len  = max(30, int(TEXT_H * ratio))
        bar_y    = TEXT_Y + int((scroll_y / (total_h - TEXT_H)) * (TEXT_H - bar_len))
        pygame.draw.rect(screen, MID_GRAY, (SCREEN_W - 10, TEXT_Y, 6, TEXT_H), border_radius=3)
        pygame.draw.rect(screen, GOLD, (SCREEN_W - 10, bar_y, 6, bar_len), border_radius=3)
 
def draw_choices():
    """Draw choice buttons."""
    n = len(choices)
    total_h = n * (CHOICE_BTN_H + CHOICE_BTN_GAP) - CHOICE_BTN_GAP
    start_x = 40
    btn_w   = SCREEN_W - 80
 
    #vertical center inside choice area
    area_h   = BAR_H + 10    # space above bottom bar
    area_top = SCREEN_H - BAR_H - total_h - 10
 
    mx, my = pygame.mouse.get_pos()
    for i, ch in enumerate(choices):
        bx = start_x
        by = area_top + i * (CHOICE_BTN_H + CHOICE_BTN_GAP)
        rect = pygame.Rect(bx, by, btn_w, CHOICE_BTN_H)
 
        hovered = rect.collidepoint(mx, my)
        if hovered:
            pygame.draw.rect(screen, GOLD, rect, border_radius=6)
            label_color = BLACK
        else:
            pygame.draw.rect(screen, MID_GRAY, rect, border_radius=6)
            pygame.draw.rect(screen, GOLD, rect, 1, border_radius=6)
            label_color = WHITE
 
        label = f"[{i+1}]  {ch['label']}"
        surf  = choice_font.render(label, True, label_color)
        screen.blit(surf, surf.get_rect(midleft=(bx + 14, by + CHOICE_BTN_H // 2)))
 
def draw_title_screen():
    draw_background(dim=False)
    draw_bars()
    draw_title_header("THE OUTSIDERS: VIDEO GAME")
    bob = int(math.sin(pygame.time.get_ticks() / 200) * 8)
    hint = small_font.render("PRESS SPACE TO START", True, WHITE)
    screen.blit(hint, hint.get_rect(center=(SCREEN_W // 2, SCREEN_H - BAR_H // 2 + bob)))
 
def draw_narrative():
    draw_background()
    draw_bars()
    title_text = LEVELS[nav_level]['title'] if nav_level in LEVELS else "THE OUTSIDERS"
    draw_title_header(title_text)
    draw_text_area()
    draw_bottom_hint("SCROLL: ↑ ↓  |  CONTINUE: SPACE or ENTER")
 
def draw_choice():
    draw_background()
    draw_bars()
    title_text = LEVELS[nav_level]['title'] if nav_level in LEVELS else "THE OUTSIDERS"
    draw_title_header(title_text)
    draw_text_area()
    draw_choices()
 
def draw_game_over():
    draw_background()
    draw_bars()
    draw_title_header("— GAME OVER —")
    draw_text_area()
    draw_bottom_hint("SPACE: Retry Level  |  ESC: Quit")
 
def draw_win():
    draw_background(dim=False)
    draw_bars()
    draw_title_header("STAY GOLD")
    draw_text_area()
 
def draw_fade(alpha):
    fade_surf = pygame.Surface((SCREEN_W, SCREEN_H))
    fade_surf.fill(BLACK)
    fade_surf.set_alpha(int(alpha))
    screen.blit(fade_surf, (0, 0))
 
state = GameState.TITLE
 
running = True
while running:
    dt = clock.tick(60)
 
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
 
        elif event.type == pygame.KEYDOWN:
 
            if state == GameState.TITLE:
                if event.key == pygame.K_SPACE:
                    state      = GameState.FADE_IN
                    fade_alpha = 0
 
            elif state == GameState.FADE_IN:
                pass  
 
            elif state == GameState.NARRATIVE:
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    advance_node()
                elif event.key == pygame.K_DOWN:
                    scroll_target = min(scroll_target + LINE_H * 3,
                        max(0, sum(LINE_H if l else LINE_H//2 for l in text_lines) - TEXT_H))
                elif event.key == pygame.K_UP:
                    scroll_target = max(0, scroll_target - LINE_H * 3)
                elif event.key == pygame.K_ESCAPE:
                    running = False
 
            elif state == GameState.CHOICE:
                key_map = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_4: 3}
                if event.key in key_map:
                    idx = key_map[event.key]
                    if idx < len(choices):
                        choose_option(idx)
                elif event.key == pygame.K_ESCAPE:
                    running = False
 
            elif state == GameState.GAME_OVER:
                if event.key == pygame.K_SPACE:
                    start_level(nav_level)
                elif event.key == pygame.K_ESCAPE:
                    running = False
 
            elif state == GameState.WIN:
                if event.key == pygame.K_ESCAPE:
                    running = False
 
            elif state == GameState.FADE_LEVEL:
                pass
 
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if state == GameState.CHOICE:
                n = len(choices)
                area_top = SCREEN_H - BAR_H - n*(CHOICE_BTN_H+CHOICE_BTN_GAP) + CHOICE_BTN_GAP - 10
                for i in range(n):
                    by = area_top + i*(CHOICE_BTN_H + CHOICE_BTN_GAP)
                    rect = pygame.Rect(40, by, SCREEN_W-80, CHOICE_BTN_H)
                    if rect.collidepoint(event.pos):
                        choose_option(i)
                        break
 
        elif event.type == pygame.MOUSEWHEEL:
            if state in (GameState.NARRATIVE, GameState.CHOICE, GameState.GAME_OVER):
                total_h = sum(LINE_H if l else LINE_H//2 for l in text_lines)
                scroll_target = max(0, min(scroll_target - event.y * LINE_H * 2,
                                           total_h - TEXT_H))
 
    # ── Update ────────────────────────────────────────────────────────────────
    if state == GameState.FADE_IN:
        fade_alpha += fade_speed
        if fade_alpha >= 255:
            fade_alpha = 255
            start_level(1)   # loads level 1 and sets state = NARRATIVE
 
    elif state == GameState.FADE_LEVEL:
        fade_alpha += fade_speed
        if fade_alpha >= 255:
            start_level(pending_level)
            fade_alpha = 255
 
    # ── Draw ──────────────────────────────────────────────────────────────────
    if state == GameState.TITLE:
        draw_title_screen()
 
    elif state == GameState.FADE_IN:
        draw_title_screen()
        draw_fade(fade_alpha)
 
    elif state == GameState.NARRATIVE:
        draw_narrative()
 
    elif state == GameState.CHOICE:
        draw_choice()
 
    elif state == GameState.GAME_OVER:
        draw_game_over()
 
    elif state == GameState.WIN:
        draw_win()
 
    elif state == GameState.FADE_LEVEL:
        if nav_level in LEVELS:
            draw_narrative()
        draw_fade(fade_alpha)
 
    pygame.display.flip()
 
pygame.quit()
sys.exit()