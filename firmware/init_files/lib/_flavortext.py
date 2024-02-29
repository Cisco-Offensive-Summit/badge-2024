# Lovingly stole from Zack Freedman's Singularitron
# https://github.com/ZackFreedman/Singularitron/blob/master/SingularitronFirmware/flavortext.h
#
# MIT License
#
# Copyright (c) 2020 Zack Freedman
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import random

class Verbs:
    def __init__(self, constructive=True):
        if constructive == True:
            self.items = [
                "Align",
                "Build",
                "Calibrat",
                "Instanc",
                "Configur",
                "Snort",
                "Microwav",
                "Tweak",
                "Wrangl",
                "Hack",
                
                "Pwn",
                "Boot",
                "Allocat",
                "Bind",
                "Revv",
                "Polish",
                "Fabricat",
                "Ping",
                "Refactor",
                "Load",
                
                "Quantify",
                "Assembl",
                "Distill",
                "Bak",
                "Receiv",
                "Unlock",
                "Compil",
                "Pressuriz",
                "Chooch",
                "Mak",
                
                "Engag",
                "Decrypt",
                "Synthesiz",
                "Predict",
                "Analyz",
                "Dispens",
                "Fir",
                "Insert",
                "Align",
                "Encourag",
                
                "Extrud",
                "Access",
                "Sharpen",
                "Enhanc",
                "Crank",
                "Stack",
                "Craft",
                "Render",
                "Mount",
                "Generat",
                
                "Implement",
                "Download",
                "Construct",
                "Wow! Amaz",
                "Moisten",
                "Customiz",
                "Compensat",
                "Buffer",
                "Transferr",
                "Induct",
                
                "Emitt",
                "Unzipp",
                "Squirt",
                "Feed",
                "Buy",
                "Spark",
                "Implant",
                "Triangulat",
                "Inject",
                "Link",
                "Brew",
                
                "Process",
                "Deploy",
                "Tun",
                "Attach",
                "Train",
                "Ignor",
                "Tapp",
                "Reload",
                "Simulat",
                "Fluff",
                
                "Fill",
                "Sort",
                "Updat",
                "Upgrad",
                "Prim",
                "Trac",
                "Inflat",
                "Wangjangl",
                "Charg",
                "Crack",
                
                "Ignor",
                "Activat",
                "Dial",
                "Pimp",
                "Collect",
                "Approach",
                "Approv",
                "Sampl",
                "Energiz",
                "Stuff"
            ]
        else:
            self.items = [
                "Deallocat",
                "Trash",
                "Unplugg",
                "Revok",
                "Forgett",
                "Discard",
                "Dropp",
                "Holster",
                "Shredd",
                "Jettison",
                
                "Dissolv",
                "Liquidat",
                "Releas",
                "Collimat",
                "Eject",
                "Ditch",
                "Leak",
                "Sell",
                "Banish",
                "Dereferenc",
                
                "Sacrific",
                "Desolder",
                "Destruct",
                "Decompil",
                "Blow",
                "Disengag",
                "Digest",
                "Smash",
                "Encrypt",
                "Crash",
                
                "Lock",
                "Purg",
                "Regrett",
                "Rewind",
                "Free",
                "Delet",
                "Clos",
                "Retract",
                "Collaps",
                "Liquefy",
                
                "Derezz",
                "Stow",
                "Archiv",
                "Suspend",
                "Suppress",
                "Clean",
                "Squash",
                "Secur",
                "Withdraw",
                "Dump",
                
                "Obfuscat",
                "Break",
                "Scrubb",
                "Abandon",
                "Flatten",
                "Stash",
                "Finish",
                "Evacuat",
                "Scrambl",
                "Recycl",
                
                "Crush",
                "Zipp",
                "Unload",
                "Disconnect",
                "Loosen",
                "Contain",
                "Debat",
                "Detach",
                "Neutraliz",
                "Salvag",
                
                "Empty",
                "Hid",
                "Disarm",
                "Pickl",
                "Disregard",
                "Yeet",
                "Scrapp",
                "Deflat",
                "Discharg",
                "Deactivat",
                
                "Steriliz",
                "Reliev",
                "Nuk",
                "Degauss",
                "Dismiss",
                "Drain",
                "Reject",
                "Nerf",
                "Pay",
                "Return",
                
                "Unstick",
                "Splitt",
                "Cancell",
                "Sham",
                "Embezzl",
                "Fling",
                "Regrett",
                "Halt",
                "Arrest",
                "Bury"
            ]
    def get_verb(self):
        return random.choice(self.items)


class Nouns:
    def __init__(self):
        self.items = [
            "content",
            "your mom",
            "the shmoo",
            "API",
            "the BJT man",
            "aesthetics",
            "backstory",
            "tactics",
            "bugs",
            "sauce",
            
            "warp drive",
            "data",
            "the funk",
            "AI",
            "crystals",
            "spaghetti",
            "fluxgate",
            "electrons",
            "loud noises",
            "wires",
            
            "bytecode",
            "the truth",
            "magic",
            "hot lava",
            "bits",
            "Brad",
            "Teensy",
            "sensors",
            "photons",
            "signal",
            
            "the planet",
            "password",
            "chips",
            "circuits",
            "privacy",
            "synergy",
            "widgets",
            "love",
            "packets",
            "reality",
            
            "lasers",
            "protocols",
            "voltage",
            "registers",
            "puns",
            "dogecoins",
            "kittens",
            "magic smoke",
            "plot device",
            "the core",
            
            "dank memes",
            "subroutines",
            "radiation",
            "steam",
            "trousers",
            "beer",
            "protocol",
            "one-liners",
            "the Gibson",
            "software",
            
            "a fat one",
            "holograms",
            "magnets",
            "inductors",
            "resistors",
            "capacitors",
            "viewers",
            "subscribers",
            "sausage",
            "my wife",
            
            "drama",
            "the future",
            "vectors",
            "the clowns",
            "a Palm Pilot",
            "5G implant",
            "monkeys",
            "breadboard",
            "Patreon",
            "money",
            
            "the Internet",
            "fluids",
            "the impostor",
            "beats",
            "dopamine",
            "fedora",
            "neural net",
            "comments",
            "ports",
            "you. Yes you",
            
            "mixtape",
            "[REDACTED]",
            "hot tub",
            "paperwork",
            "Nerf",
            "cyber-doobie",
            "the 1%",
            "the Matrix",
            "variables",
            "IP address"
        ]
    def get_noun(self):
        return random.choice(self.items)


def line(constructive=True):
    v = Verbs(constructive)
    n = Nouns()

    return v.get_verb() + "ing " + n.get_noun()
