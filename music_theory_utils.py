import numpy as np
from collections import OrderedDict

def make_dicts():
    key_names = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
    key_name_dicts = {"{}{}".format(key_names[i%12],i//12-2):i for i in range(128)}

    third_name_dicts   = {"m":3,"none":4,"sus2":2,"sus4":5}
    fifth_name_dicts   = {"none":7,"b5":6,"#5":8}
    seventh_name_dicts = {"6":9,"7":10,"maj7":11,"null":0}
    tension_name_dicts = {"addb9":13,"add9":14,"add#9":15,"add#11":18,"addb13":20,"null":0}

    chord_name_dicts = OrderedDict()
    for key in  key_names:
        for third in third_name_dicts.keys():
            for fifth in fifth_name_dicts.keys():
                for seventh in seventh_name_dicts.keys():
                    for tension in tension_name_dicts.keys():
                        key_note      = key_name_dicts[key+"2"] #ちょっと強引
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
