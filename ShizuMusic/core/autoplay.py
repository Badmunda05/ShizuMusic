# ═══════════════════════════════════════════════════════════════
#                     🎵 SHIZUMUSIC
#
#                   © 2026 BAD MUNDA
#
#                Developed with ❤️ by Bad Munda
#
#             Do not remove or alter the original credits.
#
#           Copyright © 2026 Bad Munda. All rights reserved.
#
#              
# ═══════════════════════════════════════════════════════════════

import asyncio
import logging
import random
import re
from collections import deque
from typing import Dict, List, Optional

import config
from py_yt import VideosSearch

from ShizuMusic.core.queue import add_to_queue, get_queue
from ShizuMusic.utils.db import (
    get_autoplay_lang as _db_get_lang,
    get_autoplay_mood as _db_get_mood,
    is_autoplay_enabled as _db_get_enabled,
    set_autoplay_enabled as _db_set_enabled,
    set_autoplay_lang as _db_set_lang,
    set_autoplay_mood as _db_set_mood,
)
from ShizuMusic.utils.formatters import iso_to_human, iso_to_sec, sec_to_iso
from ShizuMusic.utils.youtube import extract_video_id, related_videos

logger = logging.getLogger(__name__)
AUTOPLAY_TAG = "🔁 AutoPlay"

# ==========================================
# CONFIGURATION
# ==========================================
AUTOPLAY_BUFFER_SIZE = 6    
AUTOPLAY_MIN_BUFFER = 2  
HISTORY_SIZE = 80             
FETCH_TIMEOUT = 25  

# ==========================================
# STATE 
# ==========================================
_enabled: Dict[int, bool] = {}           
_buffer: Dict[int, List[dict]] = {}      
_history: Dict[int, deque] = {}          
_tasks: Dict[int, "asyncio.Task"] = {}  
_locks: Dict[int, asyncio.Lock] = {}   
_YT_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")

# ==========================================
# ON / OFF + LANG / MOOD 
# ==========================================
def is_autoplay(chat_id: int) -> bool:
    mode = _enabled.get(chat_id)
    if mode is not None:
        return mode
    mode = _db_get_enabled(chat_id)
    _enabled[chat_id] = mode
    return mode


def get_autoplay_lang(chat_id: int) -> str:
    return _db_get_lang(chat_id) or "auto"


def set_autoplay_lang(chat_id: int, lang: str) -> None:
    _db_set_lang(chat_id, lang)


def get_autoplay_mood(chat_id: int) -> str:
    return _db_get_mood(chat_id) or "any"


def set_autoplay_mood(chat_id: int, mood: str) -> None:
    _db_set_mood(chat_id, mood)


def start_autoplay(chat_id: int) -> None:
    """Turn AutoPlay ON for this chat."""
    _enabled[chat_id] = True
    _db_set_enabled(chat_id, True)
    current = get_queue(chat_id)
    if current:
        schedule_prefetch(chat_id, current[0])


def stop_autoplay(chat_id: int) -> None:
    """Turn AutoPlay OFF for this chat — only /autoplay off (or the toggle) calls this."""
    _enabled[chat_id] = False
    _db_set_enabled(chat_id, False)
    _buffer.pop(chat_id, None)


def reset_autoplay_state(chat_id: int) -> None:
    _buffer.pop(chat_id, None)
    task = _tasks.pop(chat_id, None)
    if task and not task.done():
        task.cancel()


def toggle_autoplay(chat_id: int) -> bool:
    enable = not is_autoplay(chat_id)
    if enable:
        start_autoplay(chat_id)
    else:
        stop_autoplay(chat_id)
    return enable


# ==========================================
# GLOBAL MUSIC DATABASE
# ==========================================
GLOBAL_MUSIC_DATABASE = {
    "hindi": {
        "romantic": [
            "Arijit Singh", "Shreya Ghoshal", "Jubin Nautiyal", "Armaan Malik", "T-Series",
            "Sonu Nigam", "KK", "Mohit Chauhan", "Atif Aslam", "Darshan Raval",
            "Vishal Mishra", "Asees Kaur", "Sunidhi Chauhan", "Monali Thakur",
            "Neeti Mohan", "Palak Muchhal", "Sachet Tandon", "Parampara Tandon",
            "Papon", "Rahat Fateh Ali Khan", "Javed Ali", "Benny Dayal",
            "Mithoon", "Tulsi Kumar", "Arijit Singh Live", "Ankit Tiwari",
            "Shaan", "Abhijeet", "Udit Narayan", "Alka Yagnik",
            "Kumar Sanu", "Sadhana Sargam", "Hariharan", "Mahalakshmi Iyer",
            "Jonita Gandhi", "Arjun Kanungo", "Dhvani Bhanushali",
            "Yasser Desai", "Stebin Ben", "Armaan Bedil"
        ],
    
        "sad": [
            "Arijit Singh", "Jubin Nautiyal", "B Praak", "T-Series",
            "KK", "Atif Aslam", "Vishal Mishra", "Ankit Tiwari",
            "Sonu Nigam", "Rahat Fateh Ali Khan", "Mohit Chauhan",
            "Darshan Raval", "Papon", "Mithoon", "Armaan Malik",
            "Javed Ali", "Stebin Ben", "Yasser Desai", "Tulsi Kumar",
            "Palak Muchhal", "Asees Kaur", "Shreya Ghoshal",
            "Neeti Mohan", "Hariharan", "Shaan"
        ],
    
        "happy": [
            "Neha Kakkar", "Tony Kakkar", "Mika Singh", "Badshah", "T-Series",
            "Benny Dayal", "Sunidhi Chauhan", "Sukhbir", "Shaan",
            "Armaan Malik", "Dhvani Bhanushali", "Jonita Gandhi",
            "Vishal Dadlani", "Shankar Mahadevan", "Salim Merchant",
            "Jubin Nautiyal", "Tulsi Kumar", "Aastha Gill",
            "Guru Randhawa", "Meet Bros", "Kanika Kapoor"
        ],
    
        "party": [
            "Neha Kakkar", "Badshah", "Raftaar", "Yo Yo Honey Singh", "T-Series",
            "Mika Singh", "Aastha Gill", "Guru Randhawa",
            "Kanika Kapoor", "Meet Bros", "DJ Chetas",
            "Nakash Aziz", "Vishal Dadlani", "Benny Dayal",
            "Tony Kakkar", "Tanishk Bagchi", "Jasmine Sandlas",
            "Akhil", "Ikka", "Bohemia"
        ],
    
        "chill": [
            "Anuv Jain", "Prateek Kuhad", "Ritviz", "T-Series Acoustic",
            "When Chai Met Toast", "The Local Train",
            "Zaeden", "Anumita Nadesan", "Sanam",
            "Papon", "Raghav Chaitanya", "Ankur Tewari",
            "Arjun Kanungo", "Dhvani Bhanushali", "Jonita Gandhi",
            "Swarathma", "Easy Wanderlings"
        ],
    
        "workout": [
            "Badshah", "Raftaar", "Divine", "T-Series",
            "Yo Yo Honey Singh", "Emiway Bantai",
            "Ikka", "King", "Krsna",
            "MC Stan", "Seedhe Maut",
            "Brodha V", "Naezy", "Bohemia",
            "Fotty Seven", "Karma", "Bella"
        ],
    
        "bhajan": [
            "T-Series Bhakti Sagar", "Shemaroo Bhakti", "Gulshan Kumar",
            "Anuradha Paudwal", "Hariharan", "Lakhbir Singh Lakkha",
            "Narendra Chanchal", "Jaya Kishori", "Devi Chitralekha",
            "Sadhvi Purnima", "Kumar Vishu", "Suresh Wadkar",
            "Anup Jalota", "Jagjit Singh"
        ],
    
        "retro": [
            "Kishore Kumar", "Lata Mangeshkar",
            "Mohammed Rafi", "Asha Bhosle",
            "Mukesh", "Manna Dey",
            "Mahendra Kapoor", "Hemant Kumar",
            "Geeta Dutt", "Talat Mahmood",
            "Jagjit Singh", "Bhupinder Singh",
            "Yesudas", "Usha Mangeshkar"
        ],
    
        "rap": [
            "Divine", "Raftaar", "Badshah", "Emiway Bantai",
            "Krsna", "MC Stan", "Seedhe Maut",
            "Naezy", "King", "Ikka",
            "Bohemia", "Brodha V", "Fotty Seven",
            "Karma", "Bella", "EPR",
            "Muhfaad", "Young Stunners"
        ],
    
        "acoustic": [
            "Anuv Jain", "Prateek Kuhad", "Ritviz",
            "Sanam", "Papon", "When Chai Met Toast",
            "Easy Wanderlings", "Ankur Tewari",
            "Anumita Nadesan", "The Local Train",
            "Arjun Kanungo", "Raghav Chaitanya"
        ],
    
        "funk": [
            "Ritviz", "Nucleya", "When Chai Met Toast",
            "Parvaaz", "The Local Train",
            "Easy Wanderlings"
        ],
    
        "phonk": [
            "Kordhell", "MoonDeity", "Dxrk",
            "INTERWORLD", "DVRST",
            "Pharmacist", "Ghostface Playa"
        ]
    },
    "english": {
        "romantic": [
            "Alan Walker", "Ed Sheeran", "Taylor Swift", "John Legend", "Sam Smith", "Shawn Mendes", "Adele",
            "Charlie Puth", "James Arthur", "Lewis Capaldi", "Harry Styles", "Zayn",
            "Niall Horan", "One Direction", "Conan Gray", "Benson Boone",
            "Olivia Rodrigo", "Lana Del Rey", "The Weeknd", "Justin Bieber",
            "Selena Gomez", "Ariana Grande", "Bruno Mars", "Sia",
            "Dean Lewis", "Stephen Sanchez", "Calum Scott", "John Mayer",
            "Jason Mraz", "Passenger", "Damiano David", "Tate McRae",
            "Lauv", "Alec Benjamin", "Khalid", "Troye Sivan",
            "Westlife", "Backstreet Boys", "Boyz II Men", "Celine Dion"
        ],
    
        "sad": [
            "Billie Eilish", "Lewis Capaldi", "Olivia Rodrigo", "Halsey", "The Weeknd",
            "Adele", "James Arthur", "Dean Lewis", "Calum Scott",
            "Sam Smith", "Conan Gray", "Alec Benjamin", "Lana Del Rey",
            "Sia", "Passenger", "Birdy", "Christina Perri",
            "Demi Lovato", "Linkin Park", "Harry Styles",
            "Zayn", "Benson Boone", "Tate McRae", "Lewis Watson",
            "Tom Odell", "Sleeping At Last", "Cigarettes After Sex"
        ],
    
        "happy": [
            "Bruno Mars", "Pharrell Williams", "Justin Bieber", "Katy Perry", "Dua Lipa",
            "Taylor Swift", "Ed Sheeran", "Ariana Grande", "Selena Gomez",
            "OneRepublic", "Maroon 5", "Imagine Dragons", "Charlie Puth",
            "Meghan Trainor", "Jason Derulo", "Pitbull", "Flo Rida",
            "Bebe Rexha", "Ava Max", "Camila Cabello", "Shawn Mendes",
            "Jonas Brothers", "Panic! At The Disco", "Walk The Moon"
        ],
    
        "party": [
            "David Guetta", "Calvin Harris", "Marshmello", "Martin Garrix", "The Chainsmokers",
            "DJ Snake", "Tiesto", "Steve Aoki", "Kygo", "Alan Walker",
            "Avicii", "Zedd", "Skrillex", "Don Diablo",
            "Hardwell", "Afrojack", "Alesso", "R3HAB",
            "Dimitri Vegas & Like Mike", "Nicky Romero", "Joel Corry",
            "Robin Schulz", "Major Lazer", "Pitbull", "Flo Rida"
        ],
    
        "chill": [
            "Alan Walker", "Kygo", "Lofi Girl", "ChilledCow",
            "Lauv", "Alec Benjamin", "Khalid", "Joji",
            "Keshi", "Jeremy Zucker", "Powfu", "JVKE",
            "Ruth B", "Cigarettes After Sex", "Novo Amor",
            "Sleeping At Last", "BoyWithUke", "Rxseboy",
            "Sasha Alex Sloan", "Conan Gray"
        ],
    
        "workout": [
            "Eminem", "Imagine Dragons", "Post Malone", "Kanye West", "Travis Scott",
            "Drake", "50 Cent", "Jay-Z", "Kendrick Lamar",
            "Future", "Lil Wayne", "21 Savage", "Metro Boomin",
            "The Weeknd", "Linkin Park", "Fall Out Boy",
            "Skillet", "NF", "Logic", "Machine Gun Kelly",
            "Denzel Curry", "A$AP Rocky", "DMX"
        ],
    
        "bhajan": [
            "Gregorian Chants", "Christian Worship Music", "Hillsong Worship",
            "Elevation Worship", "Bethel Music", "Chris Tomlin",
            "Don Moen", "Matt Redman", "Phil Wickham"
        ],
    
        "retro": [
            "Michael Jackson", "Queen", "The Beatles", "Elton John", "Madonna",
            "Whitney Houston", "George Michael", "ABBA", "Bee Gees",
            "Frank Sinatra", "Elvis Presley", "Billy Joel",
            "Bon Jovi", "Journey", "The Rolling Stones",
            "Eagles", "Fleetwood Mac", "Prince",
            "Lionel Richie", "Tina Turner", "Phil Collins",
            "Rod Stewart", "Chicago", "Earth, Wind & Fire"
        ],
    
        "rap": [
            "Eminem", "Drake", "Kendrick Lamar", "Jay-Z", "Travis Scott",
            "J. Cole", "Future", "Lil Wayne", "50 Cent",
            "21 Savage", "Logic", "NF", "A$AP Rocky",
            "Tyler, The Creator", "Snoop Dogg", "Tupac",
            "The Notorious B.I.G.", "Nas", "Joey Bada$$",
            "Denzel Curry", "Cordae", "Machine Gun Kelly",
            "Jack Harlow", "Juice WRLD", "Pop Smoke"
        ],
    
        "acoustic": [
            "Ed Sheeran", "John Mayer", "James Arthur", "Lewis Capaldi",
            "Passenger", "Jason Mraz", "Damien Rice",
            "Alec Benjamin", "Dean Lewis", "Calum Scott",
            "Shawn Mendes", "Harry Styles", "Niall Horan",
            "Birdy", "Vance Joy", "Ben Howard",
            "George Ezra", "Tom Odell", "Hozier"
        ],
    
        "funk": [
            "Bruno Mars", "Anderson .Paak", "Vulf", "Jamiroquai",
            "Earth, Wind & Fire", "Stevie Wonder", "Prince",
            "Parliament Funkadelic", "Kool & The Gang",
            "Chic", "Tower of Power", "The Brothers Johnson",
            "Daft Punk", "Silk Sonic"
        ],
    
        "phonk": [
            "Kordhell", "MoonDeity", "Dxrk", "Phonk Music",
            "DVRST", "INTERWORLD", "Ghostface Playa",
            "Pharmacist", "Sxmpra", "RAIZHELL",
            "KSLV Noh", "MC ORSEN", "DJ Smokey",
            "DJ Sacred", "Sadfriendd", "Mupp"
        ]
    },
    "punjabi": {
        "romantic": [
            "Guru Randhawa", "Diljit Dosanjh", "Hardy Sandhu", "Neha Kakkar",
            "Jass Manak", "Ammy Virk", "Karan Aujla", "AP Dhillon",
            "Shubh", "Maninder Buttar", "Jassie Gill", "Akhil",
            "Parmish Verma", "Ninja", "Jordan Sandhu", "Gurnam Bhullar",
            "Ranjit Bawa", "Kaka", "Satinder Sartaaj", "B Praak",
            "Gurinder Gill", "Shinda Kahlon", "Arjan Dhillon",
            "Amrinder Gill", "Harbhajan Mann", "Kamal Khan",
            "Rahat Fateh Ali Khan", "Afsana Khan", "Jasmine Sandlas",
            "Shipra Goyal", "Sunanda Sharma", "Nimrat Khaira",
            "Khan Bhaini", "R Nait", "Prem Dhillon", "A Kay"
        ],
    
        "sad": [
            "Sidhu Moose Wala", "B Praak", "Jass Manak", "Karan Aujla",
            "Kaka", "Amrinder Gill", "Satinder Sartaaj", "Ninja",
            "Afsana Khan", "R Nait", "Khan Bhaini", "Prem Dhillon",
            "Gurnam Bhullar", "Ammy Virk", "Arjan Dhillon",
            "Maninder Buttar", "Akhil", "Jassie Gill",
            "Harbhajan Mann", "Kamal Khan", "Rahat Fateh Ali Khan",
            "Shubh", "AP Dhillon", "Gurinder Gill"
        ],
    
        "happy": [
            "Diljit Dosanjh", "Guru Randhawa", "Mankirt Aulakh", "Ninja",
            "Ammy Virk", "Gippy Grewal", "Parmish Verma",
            "Jassie Gill", "Akhil", "Jordan Sandhu",
            "Gurnam Bhullar", "Amrinder Gill", "Sharry Mann",
            "Karan Sehmbi", "Jass Bajwa", "Ranjit Bawa",
            "Kaka", "Sunanda Sharma", "Nimrat Khaira",
            "Shipra Goyal", "Afsana Khan"
        ],
    
        "party": [
            "Badshah", "Raftaar", "Mika Singh", "Gippy Grewal",
            "Diljit Dosanjh", "Guru Randhawa", "Yo Yo Honey Singh",
            "Parmish Verma", "Mankirt Aulakh", "Jassie Gill",
            "Jass Manak", "Sharry Mann", "Jordan Sandhu",
            "Ammy Virk", "Karan Aujla", "AP Dhillon",
            "Shubh", "Bohemia", "Ikka", "Jasmine Sandlas",
            "Aastha Gill", "Navaan Sandhu", "Cheema Y"
        ],
    
        "chill": [
            "AP Dhillon", "Shinda Kahlon", "Gurinder Gill",
            "Shubh", "Karan Aujla", "Amrinder Gill",
            "Satinder Sartaaj", "Kaka", "Akhil",
            "Maninder Buttar", "Prem Dhillon", "Arjan Dhillon",
            "Navaan Sandhu", "Jordan Sandhu", "Ninja",
            "Harnoor", "Talwiinder", "Zehr Vibe"
        ],
    
        "workout": [
            "Sidhu Moose Wala", "Karan Aujla", "Diljit Dosanjh",
            "Shubh", "AP Dhillon", "Parmish Verma",
            "Mankirt Aulakh", "Navaan Sandhu", "Prem Dhillon",
            "Khan Bhaini", "R Nait", "Arjan Dhillon",
            "Bohemia", "Badshah", "Raftaar",
            "Ikka", "Cheema Y", "Gur Sidhu"
        ],
    
        "bhajan": [
            "Bhai Harjinder Singh", "Shemaroo Bhakti",
            "Bhai Jujhar Singh", "Bhai Ravinder Singh",
            "Bhai Onkar Singh", "Bhai Satvinder Singh",
            "Bhai Balwinder Singh", "Bhai Sarabjit Singh",
            "Hazoori Ragi", "Gurbani Kirtan",
            "Bhai Chamanjit Singh", "Bhai Gurpreet Singh"
        ],
    
        "retro": [
            "Gurdas Maan", "Surinder Kaur", "Mohammed Rafi",
            "Kuldeep Manak", "Yamla Jatt", "Surjit Bindrakhia",
            "Amar Singh Chamkila", "Lal Chand Yamla Jatt",
            "K Deep", "Jagmohan Kaur", "Harbhajan Mann",
            "Hans Raj Hans", "Malkit Singh", "Sardool Sikander",
            "Asa Singh Mastana"
        ],
    
        "rap": [
            "Sidhu Moose Wala", "Karan Aujla", "Raftaar", "Divine",
            "Bohemia", "Badshah", "Ikka", "AP Dhillon",
            "Shubh", "Cheema Y", "Navaan Sandhu",
            "Yo Yo Honey Singh", "King", "MC Stan",
            "Krsna", "Seedhe Maut", "Emiway Bantai",
            "Talha Anjum", "Talhah Yunus"
        ],
    
        "acoustic": [
            "AP Dhillon", "Shinda Kahlon",
            "Gurinder Gill", "Amrinder Gill",
            "Satinder Sartaaj", "Kaka",
            "Akhil", "Maninder Buttar",
            "Harnoor", "Talwiinder",
            "Zehr Vibe", "Ninja"
        ],
    
        "funk": [
            "Brar Brothers", "Malkit Singh",
            "Punjabi MC", "Diljit Dosanjh",
            "Gippy Grewal", "Jazzy B",
            "Apache Indian", "Bally Sagoo"
        ],
    
        "phonk": [
            "Kordhell", "MoonDeity", "Dxrk",
            "DVRST", "INTERWORLD",
            "Ghostface Playa", "Pharmacist",
            "Sxmpra", "MC ORSEN"
        ]
    },
    "brazilian": {
        "romantic": [
            "Anitta", "Luan Santana", "Gusttavo Lima",
            "Jorge & Mateus", "Henrique & Juliano",
            "Marília Mendonça", "Zé Neto & Cristiano",
            "Maiara & Maraisa", "Matheus & Kauan",
            "Thiaguinho", "Sorriso Maroto",
            "Ferrugem", "Ludmilla", "Péricles",
            "Paula Fernandes", "Daniel", "Leonardo",
            "Michel Teló", "Luísa Sonza", "Melim",
            "Jão", "Vitor Kley", "Tiago Iorc",
            "Roupa Nova", "Fábio Jr."
        ],
    
        "sad": [
            "Marília Mendonça", "Jorge & Mateus",
            "Henrique & Juliano", "Maiara & Maraisa",
            "Zé Neto & Cristiano", "Matheus & Kauan",
            "Gusttavo Lima", "Luan Santana",
            "Tiago Iorc", "Jão", "Melim",
            "Paula Fernandes", "Ferrugem",
            "Péricles", "Sorriso Maroto",
            "Leonardo", "Daniel", "Ludmilla"
        ],
    
        "happy": [
            "Anitta", "Luan Santana", "Wesley Safadão",
            "Ludmilla", "Luísa Sonza", "Ivete Sangalo",
            "Michel Teló", "Thiaguinho",
            "Sorriso Maroto", "Ferrugem",
            "Melim", "Vitor Kley",
            "Jorge & Mateus", "Matheus & Kauan",
            "Dennis DJ", "Pedro Sampaio",
            "MC Kevinho", "Alok"
        ],
    
        "party": [
            "MC Kevinho", "Anitta", "Alok", "Dennis DJ",
            "Pedro Sampaio", "Ludmilla",
            "Luísa Sonza", "MC Hariel",
            "MC Ryan SP", "MC IG",
            "MC Cabelinho", "MC Paiva",
            "Wesley Safadão", "Ivete Sangalo",
            "Pedro Sampaio", "KVSH",
            "Vintage Culture", "Cat Dealers",
            "Dubdogz", "Bhaskar"
        ],
    
        "chill": [
            "Bossa Nova Music", "Tom Jobim",
            "Joao Gilberto", "Elis Regina",
            "Vinicius de Moraes",
            "Nara Leão", "Toquinho",
            "Tiago Iorc", "Melim",
            "Vitor Kley", "Jão",
            "Djavan", "Gilberto Gil",
            "Caetano Veloso"
        ],
    
        "workout": [
            "MC Kevinho", "Alok", "Brazilian Bass",
            "Vintage Culture", "Cat Dealers",
            "Dubdogz", "KVSH",
            "Pedro Sampaio", "MC Hariel",
            "MC Ryan SP", "MC IG",
            "MC Cabelinho", "Ludmilla",
            "Anitta", "Dennis DJ",
            "Matuê", "Orochi"
        ],
    
        "bhajan": [
            "Padre Marcelo Rossi",
            "Aline Barros",
            "Anderson Freire",
            "Fernandinho",
            "Diante do Trono",
            "Gospel Music Brasil",
            "Casa Worship",
            "Isadora Pompeo"
        ],
    
        "retro": [
            "Tom Jobim", "Joao Gilberto", "Elis Regina",
            "Vinicius de Moraes", "Caetano Veloso",
            "Gilberto Gil", "Gal Costa",
            "Chico Buarque", "Tim Maia",
            "Djavan", "Roberto Carlos",
            "Rita Lee", "Milton Nascimento",
            "Jorge Ben Jor", "Os Mutantes"
        ],
    
        "rap": [
            "Matuê", "Teto", "WIU", "Orochi",
            "MC Cabelinho", "Filipe Ret",
            "Djonga", "BK'",
            "Xamã", "L7NNON",
            "Baco Exu do Blues",
            "Racionais MC's",
            "Projota", "Emicida",
            "Costa Gold", "Hungria Hip Hop",
            "MC Hariel", "MC Ryan SP"
        ],
    
        "acoustic": [
            "Tom Jobim", "Joao Gilberto",
            "Elis Regina", "Djavan",
            "Tiago Iorc", "Melim",
            "Vitor Kley", "Jão",
            "Gilberto Gil", "Caetano Veloso",
            "Nara Leão", "Toquinho"
        ],
    
        "funk": [
            "MC Kevinho", "MC Hariel", "KondZilla", "Matuê", "Funk Carioca",
            "MC Ryan SP", "MC IG",
            "MC Paiva", "MC Cabelinho",
            "MC Don Juan", "MC Pedrinho",
            "MC Livinho", "MC Davi",
            "MC WM", "Dennis DJ",
            "Pedro Sampaio", "Ludmilla"
        ],
    
        "phonk": [
            "Brazilian Phonk", "Phonk Brasil", "Montagem",
            "DJ GBR", "DJ Arana",
            "DJ NK3", "DJ FKU",
            "DJ Menezes", "Brazilian Drift Phonk",
            "Brazilian Cowbell", "Brazilian Funk Phonk",
            "MC GW", "MC Menor JP"
        ]
    },
    "russian": {
        "romantic": [
            "Zivert", "Artik & Asti",
            "JONY", "MOT",
            "Egor Kreed", "HammAli & Navai",
            "Ani Lorak", "Polina Gagarina",
            "Dima Bilan", "Nyusha",
            "Maksim", "LOBODA",
            "Vera Brezhneva", "Valeriya",
            "Yulianna Karaulova", "A'Studio",
            "Nyusha", "Niletto",
            "Mary Gu", "Rauf & Faik",
            "ANNA ASTI", "Mona"
        ],
    
        "sad": [
            "Miyagi & Andy Panda", "JONY",
            "Maksim", "HammAli & Navai",
            "Rauf & Faik", "Mary Gu",
            "MOT", "Polina Gagarina",
            "Dima Bilan", "Egor Kreed",
            "ANNA ASTI", "Mona",
            "Zivert", "Niletto",
            "Basta", "Macan",
            "Xolidayboy"
        ],
    
        "happy": [
            "Zivert", "Artik & Asti", "Ivanushki International",
            "Niletto", "Egor Kreed",
            "Dima Bilan", "Nyusha",
            "Polina Gagarina", "MOT",
            "ANNA ASTI", "LOBODA",
            "Yulianna Karaulova",
            "Ruki Vverh!", "Diskoteka Avariya",
            "Vremya i Steklo", "Quest Pistols",
            "Little Big"
        ],
    
        "party": [
            "Little Big", "Serebro", "DJ Smash",
            "Zivert", "Artik & Asti",
            "Niletto", "Egor Kreed",
            "Timati", "MOT",
            "ANNA ASTI", "LOBODA",
            "Ruki Vverh!", "Diskoteka Avariya",
            "Filatov & Karas",
            "Cream Soda", "Gayazovs Brothers",
            "Mia Boyka"
        ],
    
        "chill": [
            "Miyagi & Andy Panda", "JONY",
            "HammAli & Navai",
            "Rauf & Faik",
            "MOT", "Mary Gu",
            "Maksim", "Polina Gagarina",
            "Macan", "Niletto",
            "Zivert", "ANNA ASTI"
        ],
    
        "workout": [
            "Phonk Russia", "Russian Bass",
            "Timati", "Oxxxymiron",
            "Basta", "Morgenshtern",
            "Egor Kreed", "Macan",
            "Kizaru", "FACE",
            "Big Baby Tape", "Boulevard Depo",
            "Slava Marlow", "Markul",
            "LSP"
        ],
    
        "bhajan": [
            "Russian Orthodox Choir",
            "Moscow Patriarchal Choir",
            "Sretensky Monastery Choir",
            "Orthodox Chants",
            "Russian Sacred Music"
        ],
    
        "retro": [
            "Viktor Tsoi", "Kino", "Alla Pugacheva",
            "Muslim Magomaev",
            "Sofia Rotaru",
            "Valery Leontiev",
            "Yuri Antonov",
            "Zemlyane",
            "Lyube",
            "Mashina Vremeni",
            "Nautilus Pompilius",
            "DDT",
            "Vladimir Vysotsky"
        ],
    
        "rap": [
            "Basta", "Timati", "Oxxxymiron",
            "Morgenshtern", "Kizaru",
            "FACE", "Big Baby Tape",
            "Boulevard Depo", "Markul",
            "LSP", "ATL",
            "GONE.Fludd", "Slava Marlow",
            "Macan", "Friendly Thug 52 NGG",
            "OBLADAET", "Miyagi",
            "Andy Panda"
        ],
    
        "acoustic": [
            "Miyagi & Andy Panda",
            "JONY", "Rauf & Faik",
            "Mary Gu", "MOT",
            "Polina Gagarina",
            "Dima Bilan", "Maksim",
            "Zivert", "Niletto"
        ],
    
        "funk": [
            "Little Big",
            "Cream Soda",
            "Filatov & Karas",
            "Gayazovs Brothers",
            "Diskoteka Avariya",
            "Quest Pistols",
            "Ruki Vverh!"
        ],
    
        "phonk": [
            "Kordhell", "MoonDeity", "Russian Phonk", "Dxrk",
            "DVRST", "INTERWORLD",
            "Ghostface Playa",
            "Pharmacist", "Sxmpra",
            "KSLV Noh", "RAIZHELL",
            "DJ Sacred", "DJ Smokey",
            "Russian Drift Phonk",
            "Cowbell Cult"
        ]
    },
    "korean": {
        "romantic": ["HYBE LABELS", "SMTOWN", "JYP Entertainment", "BTS"],
        "sad": ["HYBE LABELS", "SMTOWN"],
        "happy": ["HYBE LABELS", "SMTOWN", "JYP Entertainment"],
        "party": ["HYBE LABELS", "SMTOWN", "YG Entertainment"],
        "chill": ["HYBE LABELS", "SMTOWN"],
        "workout": ["HYBE LABELS", "SMTOWN"],
        "bhajan": [],
        "retro": ["Seo Taiji and Boys"],
        "rap": ["HYBE LABELS", "YG Entertainment"],
        "acoustic": ["HYBE LABELS"],
        "funk": [],
        "phonk": []
    },
    "japanese": {
        "romantic": ["Sony Music Japan", "Avex", "King Records"],
        "sad": ["Sony Music Japan", "Avex"],
        "happy": ["Sony Music Japan", "Avex", "King Records"],
        "party": ["Sony Music Japan", "Avex"],
        "chill": ["Sony Music Japan", "Lofi Girl Japan"],
        "workout": ["Sony Music Japan"],
        "bhajan": [],
        "retro": ["City Pop Japan"],
        "rap": [],
        "acoustic": ["Sony Music Japan"],
        "funk": [],
        "phonk": []
    },
    "spanish": {
        "romantic": ["Sony Music Latin", "Universal Music Latino", "Shakira"],
        "sad": ["Sony Music Latin", "Universal Music Latino"],
        "happy": ["Sony Music Latin", "Universal Music Latino", "Bad Bunny", "J Balvin"],
        "party": ["Sony Music Latin", "Universal Music Latino", "Bad Bunny", "J Balvin"],
        "chill": ["Sony Music Latin"],
        "workout": ["Sony Music Latin", "Bad Bunny"],
        "bhajan": [],
        "retro": ["Selena", "Ricky Martin"],
        "rap": ["Bad Bunny", "J Balvin"],
        "acoustic": ["Sony Music Latin"],
        "funk": [],
        "phonk": []
    },
    "arabic": {
        "romantic": [
            "Rotana Music", "Mazzika", "Amr Diab",
            "Nancy Ajram", "Elissa",
            "Tamer Hosny", "Ragheb Alama",
            "Assala Nasri", "Kadim Al Sahir",
            "Wael Kfoury", "Najwa Karam",
            "Myriam Fares", "Nawal El Zoghbi",
            "Ahlam", "Balqees",
            "Majid Al Mohandis", "Hussain Al Jassmi",
            "Saad Lamjarred", "Mohamed Hamaki",
            "Sherine", "Melhem Zein",
            "Adam", "Ziad Bourji",
            "Cheb Khaled", "Faudel"
        ],
    
        "sad": [
            "Rotana Music", "Mazzika",
            "Sherine", "Elissa",
            "Assala Nasri", "Kadim Al Sahir",
            "Wael Kfoury", "Adam",
            "Tamer Hosny", "Mohamed Hamaki",
            "Majid Al Mohandis", "Hussain Al Jassmi",
            "Ragheb Alama", "Melhem Zein",
            "Ziad Bourji", "Cheb Mami",
            "Ayman Zbib"
        ],
    
        "happy": [
            "Rotana Music", "Mazzika", "Amr Diab",
            "Nancy Ajram", "Tamer Hosny",
            "Saad Lamjarred", "Mohamed Ramadan",
            "Myriam Fares", "Hussain Al Jassmi",
            "Mohamed Hamaki", "Ragheb Alama",
            "Najwa Karam", "Nawal El Zoghbi",
            "Balqees", "Ahlam",
            "Cheb Khaled", "Faudel"
        ],
    
        "party": [
            "Rotana Music", "Mazzika",
            "Amr Diab", "Saad Lamjarred",
            "Mohamed Ramadan", "Nancy Ajram",
            "Myriam Fares", "Tamer Hosny",
            "Cheb Khaled", "DJ Aseel",
            "DJ Kaboo", "Balti",
            "Wegz", "Marwan Moussa",
            "Abyusif", "Sharmoofers"
        ],
    
        "chill": [
            "Rotana Music",
            "Amr Diab", "Hussain Al Jassmi",
            "Majid Al Mohandis", "Kadim Al Sahir",
            "Sherine", "Elissa",
            "Adam", "Wael Kfoury",
            "Mohamed Hamaki", "Fairuz",
            "Marcel Khalife", "Mashrou' Leila"
        ],
    
        "workout": [
            "Mohamed Ramadan",
            "Wegz", "Marwan Moussa",
            "Abyusif", "Balti",
            "Sharmoofers", "DJ Aseel",
            "DJ Kaboo", "Saad Lamjarred",
            "Amr Diab", "Cheb Khaled"
        ],
    
        "bhajan": [
            "Mishary Rashid Alafasy",
            "Maher Zain",
            "Ahmed Bukhatir",
            "Saad Al Ghamdi",
            "Yasser Al Dosari",
            "Islamic Nasheeds",
            "Humood AlKhudher",
            "Abdul Rahman Al Ossi"
        ],
    
        "retro": [
            "Umm Kulthum", "Abdel Halim Hafez",
            "Fairuz", "Warda Al Jazairia",
            "Farid Al Atrash", "Mohamed Abdel Wahab",
            "Sabah", "Asmahan",
            "Abdel Wahab Doukkali",
            "Najat Al Saghira",
            "Sayed Darwish",
            "Talal Maddah"
        ],
    
        "rap": [
            "Wegz", "Marwan Moussa",
            "Abyusif", "Balti",
            "ElGrandeToto", "Muslim",
            "Dizzy DROS", "Shobee",
            "Stormy", "Dafencii",
            "Issam Harris", "DJ Van",
            "Flipperachi", "7liwa",
            "L7or", "Don Bigg",
            "Narcy", "The Synaptik"
        ],
    
        "acoustic": [
            "Fairuz", "Kadim Al Sahir",
            "Hussain Al Jassmi",
            "Majid Al Mohandis",
            "Sherine", "Elissa",
            "Wael Kfoury",
            "Adam", "Marcel Khalife",
            "Mohamed Hamaki"
        ],
    
        "funk": [
            "Sharmoofers",
            "Cheb Khaled",
            "Faudel",
            "Rachid Taha",
            "Amr Diab",
            "Myriam Fares",
            "Saad Lamjarred"
        ],
    
        "phonk": [
            "Arabic Phonk",
            "Arab Drift Phonk",
            "Middle East Phonk",
            "Wegz",
            "Marwan Moussa",
            "Kordhell",
            "MoonDeity",
            "Dxrk",
            "DVRST",
            "INTERWORLD"
        ]
    },
    "turkish": {
        "romantic": ["Netd Müzik", "DMC Music", "Tarkan"],
        "sad": ["Netd Müzik", "DMC Music"],
        "happy": ["Netd Müzik", "DMC Music", "Tarkan"],
        "party": ["Netd Müzik", "DMC Music"],
        "chill": ["Netd Müzik"],
        "workout": [],
        "bhajan": [],
        "retro": ["Baris Manco", "Sezen Aksu"],
        "rap": [],
        "acoustic": [],
        "funk": [],
        "phonk": []
    },
    "tamil": {
        "romantic": ["Sid Sriram", "Anirudh Ravichander", "AR Rahman", "Shreya Ghoshal"],
        "sad": ["Sid Sriram", "Anirudh Ravichander", "Yuvan Shankar Raja"],
        "happy": ["Anirudh Ravichander", "Yuvan Shankar Raja", "Harris Jayaraj"],
        "party": ["Anirudh Ravichander", "D Imman", "Harris Jayaraj"],
        "chill": ["Sid Sriram", "AR Rahman", "Pradeep Kumar"],
        "workout": ["Anirudh Ravichander", "D Imman"],
        "bhajan": ["T-Series Bhakti Tamil", "Shemaroo Bhakti"],
        "retro": ["SP Balasubrahmanyam", "KJ Yesudas", "S Janaki"],
        "rap": [],
        "acoustic": ["Sid Sriram", "Pradeep Kumar"],
        "funk": [],
        "phonk": []
    },
    "telugu": {
        "romantic": ["Sid Sriram", "Thaman S", "DSP", "Shreya Ghoshal"],
        "sad": ["Sid Sriram", "Thaman S", "MM Keeravani"],
        "happy": ["DSP", "Thaman S", "Devi Sri Prasad"],
        "party": ["DSP", "Thaman S", "Devi Sri Prasad"],
        "chill": ["Sid Sriram", "Thaman S"],
        "workout": ["DSP", "Thaman S"],
        "bhajan": ["T-Series Bhakti Telugu"],
        "retro": ["SP Balasubrahmanyam", "S Janaki"],
        "rap": [],
        "acoustic": ["Sid Sriram"],
        "funk": [],
        "phonk": []
    },
    "bengali": {
        "romantic": [
            "Arijit Singh", "Shreya Ghoshal", "Rupam Islam",
            "Anupam Roy", "Anindya Chatterjee",
            "Ishan Mitra", "Somlata Acharyya Chowdhury",
            "Monali Thakur", "Shreya Ghoshal Bengali",
            "Shaan", "Papon",
            "Timir Biswas", "Cactus",
            "Fossils", "Lagnajita Chakraborty",
            "Mekhla Dasgupta", "Iman Chakraborty",
            "Subhamita Banerjee", "Srikanto Acharya",
            "Nachiketa Chakraborty", "Arindom Chatterjee",
            "Jeet Gannguli", "Anwesshaa",
            "Usha Uthup", "Raghav Chatterjee"
        ],
    
        "sad": [
            "Arijit Singh", "Rupam Islam",
            "Anupam Roy", "Ishan Mitra",
            "Lagnajita Chakraborty",
            "Iman Chakraborty",
            "Nachiketa Chakraborty",
            "Srikanto Acharya",
            "Somlata Acharyya Chowdhury",
            "Monali Thakur",
            "Papon", "Anindya Chatterjee",
            "Fossils", "Cactus",
            "Raghav Chatterjee"
        ],
    
        "happy": [
            "Rupam Islam", "Shreya Ghoshal",
            "Arijit Singh", "Anupam Roy",
            "Anindya Chatterjee",
            "Somlata Acharyya Chowdhury",
            "Monali Thakur",
            "Usha Uthup",
            "Arindom Chatterjee",
            "Jeet Gannguli",
            "Anwesshaa",
            "Lagnajita Chakraborty",
            "Ishan Mitra"
        ],
    
        "party": [
            "Rupam Islam",
            "Fossils", "Cactus",
            "Usha Uthup",
            "Anupam Roy",
            "Arindom Chatterjee",
            "Jeet Gannguli",
            "Timir Biswas",
            "Bengali Band Music",
            "Bhoomi",
            "Chandrabindoo",
            "Lakkhichhara"
        ],
    
        "chill": [
            "Arijit Singh",
            "Anupam Roy",
            "Ishan Mitra",
            "Lagnajita Chakraborty",
            "Iman Chakraborty",
            "Somlata Acharyya Chowdhury",
            "Srikanto Acharya",
            "Monali Thakur",
            "Subhamita Banerjee",
            "Anindya Chatterjee"
        ],
    
        "workout": [
            "Rupam Islam",
            "Fossils",
            "Cactus",
            "Bhoomi",
            "Chandrabindoo",
            "Lakkhichhara",
            "Arindom Chatterjee",
            "Jeet Gannguli"
        ],
    
        "bhajan": [
            "T-Series Bhakti Bengali",
            "Anup Jalota",
            "Anuradha Paudwal",
            "Srikanto Acharya",
            "Shreya Ghoshal",
            "Bengali Kirtan",
            "Bengali Bhakti Geet",
            "Shemaroo Bhakti Bengali",
            "Mahalaya Songs",
            "Birendra Krishna Bhadra"
        ],
    
        "retro": [
            "Hemanta Mukherjee", "Sandhya Mukherjee",
            "Manna Dey",
            "Kishore Kumar",
            "Lata Mangeshkar",
            "Asha Bhosle",
            "Shyamal Mitra",
            "Arati Mukherjee",
            "Dwijen Mukhopadhyay",
            "Satinath Mukherjee",
            "Geeta Dutt",
            "Pannalal Bhattacharya",
            "Manabendra Mukhopadhyay"
        ],
    
        "rap": [
            "Bengali Rap",
            "MC Headshot",
            "Cizzy",
            "EPR",
            "Bengali Hip Hop",
            "Kobiyal",
            "Desi Bengali Rap",
            "Bengal Cypher"
        ],
    
        "acoustic": [
            "Arijit Singh",
            "Anupam Roy",
            "Ishan Mitra",
            "Lagnajita Chakraborty",
            "Iman Chakraborty",
            "Srikanto Acharya",
            "Subhamita Banerjee",
            "Anindya Chatterjee",
            "Somlata Acharyya Chowdhury"
        ],
    
        "funk": [
            "Fossils",
            "Cactus",
            "Bhoomi",
            "Chandrabindoo",
            "Lakkhichhara",
            "Usha Uthup"
        ],
    
        "phonk": [
            "Bengali Phonk",
            "Indian Phonk",
            "Desi Phonk",
            "Kordhell",
            "MoonDeity",
            "Dxrk",
            "DVRST",
            "INTERWORLD"
        ]
    },
    "marathi": {
        "romantic": ["Ajay-Atul", "Sonu Nigam", "Shreya Ghoshal"],
        "sad": ["Ajay-Atul", "Sonu Nigam"],
        "happy": ["Ajay-Atul", "Shreya Ghoshal"],
        "party": ["Ajay-Atul"],
        "chill": ["Ajay-Atul"],
        "workout": [],
        "bhajan": ["T-Series Bhakti Marathi"],
        "retro": ["Lata Mangeshkar", "Asha Bhosle"],
        "rap": [],
        "acoustic": ["Ajay-Atul"],
        "funk": [],
        "phonk": []
    },
    "gujarati": {
        "romantic": ["T-Series Gujarati", "Gujarati Music"],
        "sad": ["T-Series Gujarati"],
        "happy": ["T-Series Gujarati", "Gujarati Music"],
        "party": ["T-Series Gujarati"],
        "chill": ["T-Series Gujarati"],
        "workout": [],
        "bhajan": ["T-Series Bhakti Gujarati"],
        "retro": [],
        "rap": [],
        "acoustic": [],
        "funk": [],
        "phonk": []
    },
    "bhojpuri": {
        "romantic": [
            "T-Series Bhojpuri", "Bhojpuri Music",
            "Pawan Singh", "Khesari Lal Yadav",
            "Ritesh Pandey", "Neelkamal Singh",
            "Arvind Akela Kallu", "Ankush Raja",
            "Pramod Premi Yadav", "Gunjan Singh",
            "Samar Singh", "Chandan Chanchal",
            "Vijay Chauhan", "Dinesh Lal Yadav Nirahua",
            "Anu Dubey", "Shilpi Raj",
            "Kalpana Patowary", "Indu Sonali",
            "Priyanka Singh", "Akshara Singh",
            "Amrapali Dubey", "Kajal Raghwani",
            "Rajnandani", "Antara Singh Priyanka"
        ],
    
        "sad": [
            "T-Series Bhojpuri",
            "Pawan Singh", "Khesari Lal Yadav",
            "Ritesh Pandey", "Neelkamal Singh",
            "Arvind Akela Kallu", "Pramod Premi Yadav",
            "Gunjan Singh", "Ankush Raja",
            "Dinesh Lal Yadav Nirahua",
            "Kalpana Patowary", "Indu Sonali",
            "Shilpi Raj", "Priyanka Singh",
            "Antara Singh Priyanka"
        ],
    
        "happy": [
            "T-Series Bhojpuri", "Bhojpuri Music",
            "Pawan Singh", "Khesari Lal Yadav",
            "Ritesh Pandey", "Neelkamal Singh",
            "Arvind Akela Kallu", "Ankush Raja",
            "Pramod Premi Yadav", "Samar Singh",
            "Gunjan Singh", "Vijay Chauhan",
            "Dinesh Lal Yadav Nirahua",
            "Shilpi Raj", "Indu Sonali",
            "Priyanka Singh", "Akshara Singh",
            "Amrapali Dubey", "Kajal Raghwani"
        ],
    
        "party": [
            "T-Series Bhojpuri", "Bhojpuri Music",
            "Pawan Singh", "Khesari Lal Yadav",
            "Neelkamal Singh", "Ritesh Pandey",
            "Arvind Akela Kallu", "Ankush Raja",
            "Pramod Premi Yadav", "Samar Singh",
            "Gunjan Singh", "Chandan Chanchal",
            "Vijay Chauhan", "Shilpi Raj",
            "Akshara Singh", "Amrapali Dubey",
            "Kajal Raghwani", "Antara Singh Priyanka"
        ],
    
        "chill": [
            "Pawan Singh", "Khesari Lal Yadav",
            "Neelkamal Singh", "Ritesh Pandey",
            "Arvind Akela Kallu", "Pramod Premi Yadav",
            "Shilpi Raj", "Priyanka Singh",
            "Kalpana Patowary", "Indu Sonali"
        ],
    
        "workout": [
            "Pawan Singh", "Khesari Lal Yadav",
            "Neelkamal Singh", "Ritesh Pandey",
            "Arvind Akela Kallu", "Ankush Raja",
            "Pramod Premi Yadav", "Samar Singh",
            "Gunjan Singh", "Vijay Chauhan",
            "Chandan Chanchal"
        ],
    
        "bhajan": [
            "T-Series Bhakti Bhojpuri",
            "Pawan Singh Bhakti",
            "Khesari Lal Yadav Bhakti",
            "Devi Geet Bhojpuri",
            "Kalpana Patowary",
            "Anup Jalota",
            "Sharda Sinha",
            "Bhojpuri Bhakti Sagar",
            "Shemaroo Bhakti Bhojpuri",
            "Manoj Tiwari Bhakti"
        ],
    
        "retro": [
            "Manoj Tiwari",
            "Sharda Sinha",
            "Bharat Sharma Vyas",
            "Guddu Rangila",
            "Kalpana Patowary",
            "Malini Awasthi",
            "Dinesh Lal Yadav Nirahua",
            "Pawan Singh Classic",
            "Khesari Lal Yadav Classic"
        ],
    
        "rap": [
            "Pawan Singh",
            "Khesari Lal Yadav",
            "Neelkamal Singh",
            "Arvind Akela Kallu",
            "Samar Singh",
            "Gunjan Singh",
            "Bhojpuri Hip Hop",
            "Desi Bhojpuri Rap"
        ],
    
        "acoustic": [
            "Pawan Singh",
            "Khesari Lal Yadav",
            "Ritesh Pandey",
            "Neelkamal Singh",
            "Kalpana Patowary",
            "Sharda Sinha",
            "Indu Sonali",
            "Priyanka Singh"
        ],
    
        "funk": [
            "Bhojpuri Dance Hits",
            "Pawan Singh",
            "Khesari Lal Yadav",
            "Neelkamal Singh",
            "Samar Singh",
            "Gunjan Singh"
        ],
    
        "phonk": [
            "Bhojpuri Phonk",
            "Desi Phonk",
            "Indian Phonk",
            "Kordhell",
            "MoonDeity",
            "Dxrk",
            "DVRST"
        ]
    },
    "haryanvi": {
        "romantic": [
            "T-Series Haryanvi", "Haryanvi Hits",
            "Masoom Sharma", "Ajay Hooda",
            "Renuka Panwar", "Gulzaar Chhaniwala",
            "Amit Saini Rohtakiya", "Raju Punjabi",
            "KD Desi Rock", "Vishvajeet Choudhary",
            "Harjeet Deewana", "Khasa Aala Chahar",
            "Raj Mawar", "Anjali Raghav",
            "Komal Chaudhary", "Meenakshi Panchal",
            "Sapna Choudhary", "Surender Romio",
            "Aman Jaji", "Pranjal Dahiya",
            "Bintu Pabra", "Ashu Twinkle"
        ],
    
        "sad": [
            "T-Series Haryanvi",
            "Masoom Sharma", "Amit Saini Rohtakiya",
            "Raju Punjabi", "KD Desi Rock",
            "Khasa Aala Chahar", "Harjeet Deewana",
            "Raj Mawar", "Gulzaar Chhaniwala",
            "Vishvajeet Choudhary", "Surender Romio",
            "Bintu Pabra", "Aman Jaji"
        ],
    
        "happy": [
            "T-Series Haryanvi", "Haryanvi Hits",
            "Renuka Panwar", "Ajay Hooda",
            "Sapna Choudhary", "Masoom Sharma",
            "Raj Mawar", "Harjeet Deewana",
            "Raju Punjabi", "Vishvajeet Choudhary",
            "Amit Saini Rohtakiya", "Komal Chaudhary",
            "Ashu Twinkle", "Surender Romio",
            "Anjali Raghav", "Pranjal Dahiya"
        ],
    
        "party": [
            "T-Series Haryanvi", "Haryanvi Hits",
            "Gulzaar Chhaniwala", "KD Desi Rock",
            "Masoom Sharma", "Ajay Hooda",
            "Renuka Panwar", "Raju Punjabi",
            "Khasa Aala Chahar", "Raj Mawar",
            "Harjeet Deewana", "Amit Saini Rohtakiya",
            "Vishvajeet Choudhary", "Bintu Pabra",
            "Aman Jaji", "Ashu Twinkle",
            "MC Square", "Dhanda Nyoliwala"
        ],
    
        "chill": [
            "Khasa Aala Chahar",
            "Amit Saini Rohtakiya",
            "Masoom Sharma",
            "Harjeet Deewana",
            "Raj Mawar",
            "Surender Romio",
            "Aman Jaji",
            "Bintu Pabra",
            "Dhanda Nyoliwala"
        ],
    
        "workout": [
            "Gulzaar Chhaniwala",
            "KD Desi Rock",
            "MC Square",
            "Dhanda Nyoliwala",
            "Masoom Sharma",
            "Khasa Aala Chahar",
            "Bintu Pabra",
            "Amit Saini Rohtakiya",
            "Raj Mawar",
            "Raju Punjabi",
            "Harjeet Deewana"
        ],
    
        "bhajan": [
            "Haryanvi Bhajan",
            "Narender Kaushik",
            "Kanhaiya Mittal",
            "Anjali Jain",
            "Suresh Gola",
            "Sonotek Bhakti",
            "T-Series Bhakti Haryanvi",
            "Shemaroo Bhakti"
        ],
    
        "retro": [
            "Rajkishan Agwanpuriya",
            "Ranbir Badwasaniya",
            "Satbir Ahlawat",
            "Master Satbir",
            "Bale Ram Halwai",
            "Haryanvi Ragni",
            "Pandit Lakhmichand",
            "Dayachand Mayna"
        ],
    
        "rap": [
            "MC Square",
            "KD Desi Rock",
            "Dhanda Nyoliwala",
            "Gulzaar Chhaniwala",
            "Bintu Pabra",
            "Aman Jaji",
            "Khasa Aala Chahar",
            "Desi Haryanvi Rap",
            "Haryanvi Hip Hop"
        ],
    
        "acoustic": [
            "Masoom Sharma",
            "Harjeet Deewana",
            "Raj Mawar",
            "Amit Saini Rohtakiya",
            "Surender Romio",
            "Khasa Aala Chahar",
            "Renuka Panwar",
            "Komal Chaudhary"
        ],
    
        "funk": [
            "Gulzaar Chhaniwala",
            "KD Desi Rock",
            "MC Square",
            "Dhanda Nyoliwala",
            "Masoom Sharma",
            "Khasa Aala Chahar"
        ],
    
        "phonk": [
            "Haryanvi Phonk",
            "Desi Phonk",
            "Indian Drift Phonk",
            "MC Square",
            "Dhanda Nyoliwala",
            "Kordhell",
            "MoonDeity",
            "Dxrk",
            "DVRST",
            "INTERWORLD"
        ]
    },
    "urdu": {
        "romantic": ["Coke Studio Pakistan", "Atif Aslam", "Ali Zafar"],
        "sad": ["Coke Studio Pakistan", "Atif Aslam"],
        "happy": ["Coke Studio Pakistan", "Ali Zafar"],
        "party": ["Coke Studio Pakistan"],
        "chill": ["Coke Studio Pakistan"],
        "workout": [],
        "bhajan": [],
        "retro": ["Nusrat Fateh Ali Khan", "Mehdi Hassan"],
        "rap": [],
        "acoustic": ["Coke Studio Pakistan"],
        "funk": [],
        "phonk": []
    },
    "french": {
        "romantic": ["NRJ Hits", "Skyrock", "Edith Piaf"],
        "sad": ["NRJ Hits", "Skyrock"],
        "happy": ["NRJ Hits", "Skyrock"],
        "party": ["NRJ Hits", "Skyrock"],
        "chill": ["NRJ Hits"],
        "workout": [],
        "bhajan": [],
        "retro": ["Edith Piaf", "Jacques Brel"],
        "rap": ["Skyrock"],
        "acoustic": [],
        "funk": [],
        "phonk": []
    },
    "chinese": {
        "romantic": ["Tencent Music", "Jay Chou", "Eason Chan"],
        "sad": ["Tencent Music", "Jay Chou"],
        "happy": ["Tencent Music", "Jay Chou"],
        "party": ["Tencent Music"],
        "chill": ["Tencent Music"],
        "workout": [],
        "bhajan": [],
        "retro": ["Teresa Teng"],
        "rap": [],
        "acoustic": ["Jay Chou"],
        "funk": [],
        "phonk": []
    }
}
# ==========================================
# CHANNEL VIDEO FETCHER
# ==========================================
async def fetch_channel_videos(channel_name: str, max_results: int = 20) -> list:
    try:
        search = VideosSearch(channel_name, limit=max_results)
        res = await search.next()

        results = []
        if not res or not res.get("result"):
            return results

        for video in res["result"]:
            try:
                channel_info = video.get("channel", {})
                channel_title = channel_info.get("name", "").lower() if channel_info else ""

                if channel_name.lower() not in ["t-series", "sony music", "zee music", "shemaroo", "rotana", "mazzika", "netd"]:
                    if channel_name.lower().split()[0] not in channel_title:
                        continue

                results.append({
                    "id": video.get("id"),
                    "title": video.get("title"),
                    "duration": video.get("duration"),
                    "channel": channel_title
                })
            except Exception:
                continue

        return results
    except Exception:
        return []

# ==========================================
# FILTER FUNCTIONS
# ==========================================
def filter_by_mood(videos: list, mood: str) -> list:
    if mood == "any" or not mood:
        return videos

    filtered = []
    mood_keywords = {
        "romantic": ['love', 'pyaar', 'ishq', 'mohabbat', 'romantic', 'dil', 'sanam', 'tera', 'meri', 'heart'],
        "sad": ['sad', 'dard', 'judaa', 'tanha', 'alone', 'broken', 'tears', 'heartbroken', 'cry'],
        "happy": ['party', 'dance', 'nacho', 'bhangra', 'celebration', 'happy', 'item', 'fun'],
        "party": ['party', 'club', 'dj', 'remix', 'dance', 'bass', 'rave'],
        "chill": ['chill', 'relax', 'lofi', 'acoustic', 'unplugged', 'soft', 'slow', 'ambient'],
        "workout": ['workout', 'gym', 'motivation', 'energy', 'power', 'beast', 'pump', 'fitness'],
        "bhajan": ['bhajan', 'aarti', 'stotram', 'mantra', 'shiv', 'krishna', 'ram', 'hanuman', 'devotional', 'god'],
        "retro": ['old', 'classic', 'vintage', '70s', '80s', '90s', 'retro'],
        "rap": ['rap', 'hip hop', 'freestyle', 'diss', 'flow', 'bars'],
        "acoustic": ['acoustic', 'unplugged', 'live acoustic', 'guitar', 'piano'],
        "funk": ['funk', 'carioca', 'baile', 'mc ', 'beat'],
        "phonk": ['phonk', 'drift', 'cowbell', 'brazilian phonk', 'russian phonk']
    }

    keywords = mood_keywords.get(mood, [])
    for video in videos:
        title = video.get("title", "").lower()
        if any(word in title for word in keywords):
            filtered.append(video)

    return filtered if filtered else videos

def filter_by_language(videos: list, lang: str) -> list:
    if lang == "auto" or not lang:
        return videos

    filtered = []
    lang_keywords = {
        "hindi": ['hindi', 'bollywood'],
        "punjabi": ['punjabi', 'jatt', 'munde', 'kudi', 'bhangra'],
        "english": ['english', 'pop', 'rock', 'hip hop'],
        "tamil": ['tamil', 'kollywood'],
        "telugu": ['telugu', 'tollywood'],
        "kannada": ['kannada', 'sandalwood'],
        "malayalam": ['malayalam', 'mollywood'],
        "bengali": ['bengali'],
        "marathi": ['marathi'],
        "gujarati": ['gujarati'],
        "bhojpuri": ['bhojpuri'],
        "haryanvi": ['haryanvi'],
        "urdu": ['urdu', 'pakistani'],
        "arabic": ['arabic'],
        "turkish": ['turkish'],
        "korean": ['korean', 'kpop'],
        "japanese": ['japanese', 'jpop', 'anime'],
        "spanish": ['spanish', 'latin'],
        "french": ['french'],
        "brazilian": ['brazilian', 'portuguese', 'funk carioca', 'sertanejo'],
        "russian": ['russian'],
        "chinese": ['chinese', 'mandopop']
    }

    keywords = lang_keywords.get(lang, [])
    for video in videos:
        title = video.get("title", "").lower()
        channel = video.get("channel", "").lower()

        if lang == "hindi":
            other_indian = ['punjabi', 'tamil', 'telugu', 'kannada', 'malayalam', 'bengali', 'marathi', 'gujarati', 'bhojpuri', 'haryanvi']
            if not any(word in title for word in other_indian) and not any(word in channel for word in other_indian):
                filtered.append(video)
        else:
            if any(word in title for word in keywords) or any(word in channel for word in keywords):
                filtered.append(video)

    return filtered if filtered else videos

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def extract_song_name(title: str) -> str:
    if not title:
        return ""
    title = title.lower()
    title = re.sub(r'\([^)]*\)', '', title)
    title = re.sub(r'\[[^\]]*\]', '', title)
    for sep in [' | ', ' - ', ' by ', ' from ', ' ft. ', ' feat. ']:
        if sep in title:
            title = title.split(sep)[0]
    noise = {'official', 'video', 'audio', 'full', 'song', 'title', 'hd', '4k', '8k',
             'new', 'latest', 'lyrics', 'lyrical'}
    words = [w for w in title.split() if w not in noise]
    cleaned = ''.join(c for c in ' '.join(words) if c.isalnum() or c.isspace())
    return ' '.join(cleaned.split()).strip()


def is_same_song(title1: str, title2: str) -> bool:
    song1 = extract_song_name(title1)
    song2 = extract_song_name(title2)
    if not song1 or not song2:
        return False
    if song1 == song2:
        return True
    words1 = set(song1.split())
    words2 = set(song2.split())
    if not words1 or not words2:
        return False
    common = words1 & words2
    similarity = len(common) / min(len(words1), len(words2))
    return similarity >= 0.7


_BAD_PHRASES = [
    # playlists / compilations
    "jukebox", "mashup", "compilation", "playlist", "medley",
    "non stop", "non-stop", "nonstop", "megamix", "full album", "top 10", "top 20",
    "top 50", "best of", "hits of", "songs of",
    # movies / promos
    "full movie", "movie clip", "movie scene", "official trailer", "trailer",
    "teaser", "promo", "making of", "behind the scenes", "bts video",
    # live streams / loops
    "live stream", "livestream", "watch live", "streaming now", "24/7", "24x7",
    "hour loop", "1 hour", "10 hours", "hours of",
    # talks / reactions
    "podcast", "interview", "press conference", "reaction", "reacts to",
    "review", "explained",
    # shorts / gaming / news / random
    "#shorts", "youtube shorts", "short video", "gameplay", "walkthrough",
    "gaming", "breaking news", "news update", "food vlog", "travel vlog",
    "recipe", "cooking",
]
_BAD_RE = re.compile(
    r"(?<![a-z0-9])(?:" + "|".join(re.escape(p) for p in _BAD_PHRASES) + r"|mix)(?![a-z0-9])"
)


def is_bad_song(title: str, duration_sec: int) -> bool:
    """True for anything that is not a normal single song."""
    if not title:
        return True
    t = title.lower().strip()
    if t.startswith("http") or "youtu.be/" in t or "youtube.com/" in t:
        return True
    # "mix" only as a whole word, so "Remix" versions are still allowed
    if _BAD_RE.search(t):
        return True
    if duration_sec < 90 or duration_sec > 900:
        return True
    return False


def _seed_id(track: Optional[dict]) -> Optional[str]:
    """YouTube id of a queue item (None if it can't be determined)."""
    if not track:
        return None
    vid = track.get("vidid")
    if isinstance(vid, str) and _YT_ID.match(vid):
        return vid
    vid = extract_video_id(track.get("url") or "")
    return vid if isinstance(vid, str) and _YT_ID.match(vid) else None


def _to_seconds(value) -> int:
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    try:
        return sum(
            int(x) * 60 ** i
            for i, x in enumerate(reversed(str(value).strip().split(":")))
        )
    except Exception:
        return 0


def _fmt_duration(sec: int) -> str:
    sec = int(sec)
    h, rest = divmod(sec, 3600)
    m, s = divmod(rest, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def _candidate(vid, title, duration, channel="") -> Optional[dict]:
    if not vid or not title:
        return None
    sec = _to_seconds(duration)
    return {
        "id": vid,
        "title": str(title).strip(),
        "duration_sec": sec,
        "duration_min": _fmt_duration(sec) if sec else "0:00",
        "channel": (channel or "").lower(),
    }


def remember(chat_id: int, track: Optional[dict]):
    """Remember a played song so autoplay never repeats it."""
    if not track:
        return
    vid = _seed_id(track)
    title = track.get("title") or ""
    hist = _history.setdefault(chat_id, deque(maxlen=HISTORY_SIZE))
    if hist and hist[-1]["vidid"] == vid and hist[-1]["title"] == title:
        return
    hist.append({"vidid": vid, "title": title})


def _is_dup(chat_id: int, vid: str, title: str) -> bool:
    """Already played, already queued, or just another upload of the same song."""
    hist = list(_history.get(chat_id, ()))
    if any(h["vidid"] == vid for h in hist):
        return True
    known = [h["title"] for h in hist[-15:]]
    for item in get_queue(chat_id) or []:
        item_vid = extract_video_id(item.get("url") or "")
        if item_vid == vid:
            return True
        known.append(item.get("title") or "")
    return any(is_same_song(t, title) for t in known if t)


def _usable(cands: List[dict], chat_id: int, seed_vid: Optional[str]) -> List[dict]:
    seen, out = set(), []
    for c in cands:
        cid = c["id"]
        if cid in seen or cid == seed_vid:
            continue
        seen.add(cid)
        if is_bad_song(c["title"], c["duration_sec"]):
            continue
        if c["duration_sec"] > config.MAX_DURATION_SECONDS:
            continue
        if _is_dup(chat_id, cid, c["title"]):
            continue
        out.append(c)
    return out


def _soft_shuffle(items: List[dict], group: int = 3) -> List[dict]:
    """Keep the 'most related first' order but avoid the same chain every time."""
    out = []
    for i in range(0, len(items), group):
        chunk = items[i:i + group]
        random.shuffle(chunk)
        out.extend(chunk)
    return out


def _build_queries(seed_title: str, lang: str, mood: str) -> List[str]:
    name = extract_song_name(seed_title)
    queries = []
    if name:
        queries += [f"{name} similar songs", f"songs like {name}"]
    l = "" if lang in ("", "auto") else lang
    m = "" if mood in ("", "any") else mood
    if l or m:
        queries.append(f"{l} {m} songs".strip())
    if not queries:
        queries.append("latest songs")
    return queries


async def _search(query: str, limit: int = 15) -> List[dict]:
    try:
        res = await VideosSearch(query, limit=limit).next()
    except Exception as e:
        logger.warning(f"[AutoPlay] search '{query}' failed: {e}")
        return []
    out = []
    for v in (res or {}).get("result") or []:
        c = _candidate(
            v.get("id"),
            v.get("title"),
            v.get("duration"),
            (v.get("channel") or {}).get("name"),
        )
        if c:
            out.append(c)
    return out


async def _channel_candidates(lang: str, mood: str, count: int = 3) -> List[dict]:
    """Optional: songs from the curated channel list for the chosen language/mood."""
    moods = GLOBAL_MUSIC_DATABASE.get(lang) or {}
    if not moods:
        return []
    channels = moods.get(mood) if mood not in ("", "any") else None
    if not channels:
        channels = random.choice([c for c in moods.values() if c] or [[]])
    if not channels:
        return []
    picked = random.sample(channels, min(count, len(channels)))
    lists = await asyncio.gather(
        *[fetch_channel_videos(ch, max_results=15) for ch in picked],
        return_exceptions=True,
    )
    out = []
    for lst in lists:
        if isinstance(lst, list):
            for v in lst:
                c = _candidate(v.get("id"), v.get("title"), v.get("duration"), v.get("channel"))
                if c:
                    out.append(c)
    return out


# ==========================================
# FINDING SONGS
# ==========================================
async def fetch_candidates(chat_id: int, seed: dict) -> List[dict]:
    """Best next songs for `seed`: YouTube's own suggestions first, search as backup."""
    lang = get_autoplay_lang(chat_id)
    mood = get_autoplay_mood(chat_id)
    prefs = lang not in ("", "auto") or mood not in ("", "any")
    seed_vid = _seed_id(seed)
    seed_title = (seed or {}).get("title") or ""

    def apply_prefs(items):
        return filter_by_language(filter_by_mood(items, mood), lang) if prefs else items

    pool: List[dict] = []
    if seed_vid:
        try:
            for r in await related_videos(seed_vid, limit=30):
                c = _candidate(r.get("id"), r.get("title"), r.get("duration"), r.get("channel"))
                if c:
                    pool.append(c)
        except Exception as e:
            logger.warning(f"[AutoPlay] related lookup failed: {e}")
    usable = _usable(apply_prefs(pool), chat_id, seed_vid)

    if len(usable) < AUTOPLAY_BUFFER_SIZE:
        jobs = [_search(q) for q in _build_queries(seed_title, lang, mood)]
        if prefs and lang not in ("", "auto"):
            jobs.append(_channel_candidates(lang, mood))
        extra: List[dict] = []
        for r in await asyncio.gather(*jobs, return_exceptions=True):
            if isinstance(r, list):
                extra += r
        usable = _usable(apply_prefs(pool + extra), chat_id, seed_vid)

    if not usable:
        # last resort so the music never stops
        base = "" if lang in ("", "auto") else f"{lang} "
        extra = []
        for r in await asyncio.gather(
            _search(f"{base}trending songs"),
            _search(f"{base}latest hit songs"),
            return_exceptions=True,
        ):
            if isinstance(r, list):
                extra += r
        usable = _usable(pool + extra, chat_id, seed_vid)

    return _soft_shuffle(usable)


# ==========================================
# BUFFER + BACKGROUND PREFETCH
# ==========================================
async def _fill_buffer(chat_id: int, seed: dict):
    try:
        cands = await fetch_candidates(chat_id, seed)
    except Exception as e:
        logger.warning(f"[AutoPlay] fetch failed: {e}")
        return
    if not is_autoplay(chat_id):      # switched off while we were searching
        return
    buf = _buffer.setdefault(chat_id, [])
    for c in cands:
        if len(buf) >= AUTOPLAY_BUFFER_SIZE:
            break
        if any(b["id"] == c["id"] or is_same_song(b["title"], c["title"]) for b in buf):
            continue
        buf.append(c)


def _start_fill(chat_id: int, seed: dict) -> "asyncio.Task":
    task = _tasks.get(chat_id)
    if task and not task.done():
        return task
    task = asyncio.create_task(_fill_buffer(chat_id, seed))
    _tasks[chat_id] = task

    def _cleanup(t, cid=chat_id):
        if _tasks.get(cid) is t:
            _tasks.pop(cid, None)

    task.add_done_callback(_cleanup)
    return task


def schedule_prefetch(chat_id: int, track: Optional[dict]):
    """Call whenever a new song STARTS playing. Non-blocking, never raises."""
    try:
        if not track or not is_autoplay(chat_id):
            return
        remember(chat_id, track)
        if str(track.get("requester")) != AUTOPLAY_TAG:
            # a person picked this song: forget suggestions made for older songs
            _buffer.pop(chat_id, None)
        if len(_buffer.get(chat_id, [])) >= AUTOPLAY_MIN_BUFFER:
            return
        _start_fill(chat_id, track)
    except Exception as e:
        logger.warning(f"[AutoPlay] prefetch error: {e}")


def _pop_valid(chat_id: int) -> Optional[dict]:
    buf = _buffer.get(chat_id) or []
    while buf:
        c = buf.pop(0)
        if not _is_dup(chat_id, c["id"], c["title"]):
            return c
    return None


# ==========================================
# MAIN ENTRY
# ==========================================
async def autoplay_next(chat_id: int, last_track: Optional[dict]) -> bool:
    """
    Call when the queue is empty (song ended / last song skipped).
    Puts one related song in the queue and returns True, else returns False.
    """
    try:
        if not last_track or not is_autoplay(chat_id):
            return False
        lock = _locks.setdefault(chat_id, asyncio.Lock())
        async with lock:
            remember(chat_id, last_track)
            item = _pop_valid(chat_id)
            if not item:
                task = _start_fill(chat_id, last_track)
                try:
                    await asyncio.wait_for(asyncio.shield(task), FETCH_TIMEOUT)
                except Exception:
                    pass
                item = _pop_valid(chat_id)
            if not item:
                try:
                    await asyncio.wait_for(_fill_buffer(chat_id, last_track), FETCH_TIMEOUT)
                except Exception:
                    pass
                item = _pop_valid(chat_id)
            if not item:
                return False
            add_to_queue(chat_id, {
                "url": f"https://www.youtube.com/watch?v={item['id']}",
                "title": item["title"],
                "duration": item["duration_min"],
                "duration_seconds": item["duration_sec"],
                "requester": AUTOPLAY_TAG,
                "requester_id": last_track.get("requester_id") or 0,
                "thumbnail": f"https://i.ytimg.com/vi/{item['id']}/hqdefault.jpg",
                "vidid": item["id"],
            })
            remember(chat_id, {"vidid": item["id"], "title": item["title"]})
            return True
    except Exception as e:
        logger.warning(f"[AutoPlay] autoplay_next failed: {e}")
        return False


AUTOPLAY_LANGS = ["auto"] + list(GLOBAL_MUSIC_DATABASE.keys())
AUTOPLAY_MOODS = ["any"] + list(GLOBAL_MUSIC_DATABASE["hindi"].keys())
