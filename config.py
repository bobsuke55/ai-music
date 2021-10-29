import numpy as np
from music_theory_utils import make_dicts,inversion

bar_reso         = 96 # 1小節の解像度　　一小節の分解能は96で良いのでは？
half_reso = bar_reso//2
quarter_reso     = bar_reso//4  # 4部音符の解像度 
quarter_tri_reso = quarter_reso//3
quaver_reso      = quarter_reso//2 #8部音符の解像度
quaver_tri_reso  = quaver_reso//3
bar_reso         = int(bar_reso*3/4)

bar_num          = 8     # 小節数
all_reso         = bar_num * bar_reso #8 * 96
tempo            = 120    #bpm
pitch_reso = 128    # 鍵盤の数
note_velocity = 127
tempos = tempo*np.ones( [all_reso,1] )

note2long_dicts = {"bar":bar_reso,"half":half_reso,
"quarter":quarter_reso,"quaver":quaver_reso,
"quaver_tri":quaver_tri_reso,"quarter_tri":quarter_tri_reso,
}

long2note_dicts = {val:key for key, val in note2long_dicts.items()}
key2array_dicts,chord2array_dicts = make_dicts()
chord2array_dicts = {key:inversion(np.array(val),course=48) for key,val in chord2array_dicts.items() }