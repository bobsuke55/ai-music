import numpy as np
from collections import OrderedDict
from config import *

def make_backing_rhythm():
    events_choice     = {"bar_note":1.0,"quaver_note":0.0,"quarter_rest":0.0,"quaver_rest":0.0}
    rhythm_list       = []
    note_dulation_sum = 0
    
    while all_reso > note_dulation_sum:
        note_char = np.random.choice(list( events_choice.keys()) ,p=list(events_choice.values()),replace=True)
        long, switch = note_char.split("_")
        note_dulation = note2long_dicts[long]
        note_dulation_sum += note_dulation
        rhythm_list.append(note_char)
    
    if note_dulation_sum > all_reso:
        diff_dulation = note_dulation_sum - all_reso
        rhythm_list[-1] = long2note_dicts[diff_dulation] + "_" + switch
    
    return rhythm_list

def make_backing_chord():
    chord_list = ["C","G","Am7","Em7","F","C","Fadd9","G7"]
    return chord_list

def chord2pianorll(rhythm_list,pitch_list,pad_end=True):
    bar_pianoroll = np.zeros([all_reso,pitch_reso])
    note_start = 0
    note_end   = 0
    note_list  = [note.split("_")[0] for note in rhythm_list]
    
    for note, chord_name in zip(note_list, pitch_list):
        note_dulation = note2long_dicts[note]
        note_end = note_start + note_dulation

        chord_array = chord2array_dicts[chord_name]
        bar_pianoroll[note_start:note_end,chord_array] = 127
        bar_pianoroll[note_start:note_end,chord_array[0] - 12] = 127 # ベース音の追加

        if pad_end:
            bar_pianoroll[note_end-1,:] = 0 
            note_start = note_end 
                   
    return bar_pianoroll

def make_motief_rhythm():
    events_choice = {"quarter_note":0.6,"quaver_note":0.3,"quarter_rest":0.05,"quaver_rest":0.05}
    rhythm_list = []
    note_dulation_sum = 0
    
    while bar_reso > note_dulation_sum:
        note_char = np.random.choice(list( events_choice.keys()) ,p=list(events_choice.values()),replace=True)
        long, switch = note_char.split("_")
        note_dulation = note2long_dicts[long]
        note_dulation_sum += note_dulation

        rhythm_list.append(note_char)
    
    if note_dulation_sum > bar_reso:
        diff_dulation = note_dulation_sum - bar_reso
        rhythm_list[-1] = long2note_dicts[diff_dulation] + "_" + switch
    
    return rhythm_list

def make_motief_pitch(rhythm_list):
    pentas_keys  = ["C","D","E","G","A"]
    octave_nums  = ["4","5"]
    pentas_choice = {i+j:1/(len(pentas_keys)*len(octave_nums)) for i in pentas_keys for j in octave_nums}
    pitch_list = []
    for rhythm in rhythm_list:
        [long, switch] = rhythm.split("_")
        
        if switch == "rest":
            melo = "null"
        else:
            melo  = np.random.choice( list(pentas_choice.keys()),p=list(pentas_choice.values()),replace=True)
        
        pitch_list.append(melo)
    
    return pitch_list

def events2pianoroll(rhythm_list, pitch_list,pad_end=True):
    bar_pianoroll = np.zeros([bar_reso,pitch_reso])
    note_start = 0
    note_end = 0
    note_list = [note.split("_")[0] for note in rhythm_list]
    for note, melo in zip(note_list, pitch_list):
        note_dulation = note2long_dicts[note]
        note_end = note_start + note_dulation
        if melo != "null":
            pitch = key2array_dicts[melo]
            bar_pianoroll[note_start:note_end,pitch] = note_velocity 
            if pad_end: 
                bar_pianoroll[note_end-1,pitch] = 0 
        note_start = note_end
    return bar_pianoroll

def make_motief():
    rhythm_list = make_motief_rhythm()
    pitch_list = make_motief_pitch(rhythm_list)
    pianoroll = events2pianoroll(rhythm_list, pitch_list)
    return rhythm_list, pitch_list, pianoroll