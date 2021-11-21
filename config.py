import numpy as np
from music_theory_utils import make_dicts,inversion

bar_reso         = 96 # 1小節の解像度　　一小節の分解能は96で良いのでは？
half_reso = bar_reso//2
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
pitch_reso = 128    # 鍵盤の数
note_velocity = 127
tempos = tempo*np.ones( [all_reso,1] )

dulation_char2num_dicts = {
    "bar":bar_reso,"half":half_reso,
    "quarter":quarter_reso,"dotted_quarter":dotted_quarter_reso,
    "quaver":quaver_reso}
    #"dotted_quaver":dotted_quaver_reso,
    #"quarter_tri":quarter_tri_reso ,"quaver_tri":quaver_tri_reso,
    #"semiquaver":semiquaver_reso}

dulation_num2char_dicts = {val:key for key, val in dulation_char2num_dicts.items()}

pitch_char2num_dicts,chord_char2array_dicts = make_dicts()
pitch_num2char_dicts     = {val:key for key,val in pitch_char2num_dicts.items()}
chord_char2array_dicts = {key:inversion(np.array(val),course=48) for key,val in chord_char2array_dicts.items() }