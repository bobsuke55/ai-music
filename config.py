import numpy as np
import itertools

bar_reso         = 96 # 1小節の解像度　　一小節の分解能は96で良いのでは？
half_reso        = bar_reso//2
quarter_reso     = bar_reso//4  # 4部音符の解像度 
dotted_quarter_reso     = int( quarter_reso * 1.5 )
quarter_tri_reso = quarter_reso//3 *2 #
quaver_reso      = quarter_reso//2 #8部音符の解像度
dotted_quaver_reso = int(quaver_reso * 1.5) #8部音符の解像度
quaver_tri_reso  = quaver_reso//3 *2
semiquaver_reso  = quaver_reso//2

bar_num          = 8     # 小節数
all_reso         = bar_num * bar_reso #8 * 96
tempo            = 120    #bpm
pitch_reso       = 128    #鍵盤の数
note_velocity    = 127
tempos           = tempo*np.ones( [all_reso,1] )
    
def make_dicts():
    key_names = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
    key_name_dicts = {"{}{:+d}".format(key_names[i%12],i//12-2):i for i in range(128)}

    third_name_dicts   = {"m":3,"none":4,"sus2":2,"sus4":5}
    fifth_name_dicts   = {"none":7,"b5":6,"#5":8}
    seventh_name_dicts = {"6":9,"7":10,"maj7":11,"null":0}
    tension_name_dicts = {"addb9":13,"add9":14,"add#9":15,"add#11":18,"addb13":20,"null":0}

    chord_name_dicts = {}
    for key in  key_names:
        for third in third_name_dicts.keys():
            for fifth in fifth_name_dicts.keys():
                for seventh in seventh_name_dicts.keys():
                    for tension in tension_name_dicts.keys():
                        key_note      = key_name_dicts[key+"+2"] #ちょっと強引
                        third_note    = key_note + third_name_dicts[third]
                        fifth_note    = key_note + fifth_name_dicts[fifth]
                        seventh_note  = key_note + seventh_name_dicts[seventh]
                        tension_note  = key_note + tension_name_dicts[tension]
                        chord_array = np.array( list({key_note,third_note,fifth_note,seventh_note,tension_note}) )
                        chord_array.sort()
                        #set{}によって，同じ要素を消す．seventhとtenstionがnullの場合，key_noteと同じ値になる．

                        if "sus" in third:
                            chord_name  = key+seventh+third+fifth+tension
                        else:
                            chord_name  = key+third+seventh+fifth+tension

                        chord_name  = chord_name.replace("none","")
                        chord_name  = chord_name.replace("null","")
                        
                        if third == "m" and fifth == "b5" and seventh == "6" and tension == "null":
                            chord_name = chord_name.replace("m6b5", "dim7")
                        if third == "m" and fifth == "b5" and seventh == "null" and tension == "null":
                            chord_name = chord_name.replace("mb5", "dim")
                        if third == "none" and fifth == "#5" and seventh == "null" and tension == "null":
                            chord_name = chord_name.replace("#5", "aug")
                        
                        chord_name_dicts[chord_name] = chord_array
                        
    return key_name_dicts,chord_name_dicts

def inversion(val,course=48):
    val_inversion = np.array( [i%12 for i in val] ) + course
    return val_inversion

dulation_char2num_dicts = {
    "bar":bar_reso,"half":half_reso,
    "quarter":quarter_reso,"dotted_quarter":dotted_quarter_reso,
    "quaver":quaver_reso,"dotted_quaver":dotted_quaver_reso,
    "quarter_tri":quarter_tri_reso ,"quaver_tri":quaver_tri_reso,
    "semiquaver":semiquaver_reso
}
dulation_num2char_dicts  = {val:key for key, val in dulation_char2num_dicts.items()}
pitch_char2num_dicts,chord_char2array_dicts = make_dicts()
pitch_char2num_dicts["N"] = -1
pitch_num2char_dicts     = {val:key for key,val in pitch_char2num_dicts.items()}
chord_char2array_dicts   = {key:inversion(np.array(val),course=48) for key,val in chord_char2array_dicts.items() }