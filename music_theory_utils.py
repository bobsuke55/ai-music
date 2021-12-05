import numpy as np
import itertools
import copy
import config

#音符
class Note:
    def __init__(self,dulation_char,onoff_char,pitch_char="C-2",bpm=config.tempo):
        self.dulation_char  = dulation_char # quaver, (長さ) "quaver"
        self.onoff_char     = onoff_char # on or off 
        self.pitch_char     = pitch_char #'C5'
        self.bpm       = bpm
        self.char2num()
        
    def char2num(self): ##charの状態をnumに反映させる
        self.dulation_num  = config.dulation_char2num_dicts[self.dulation_char]
        self.onoff_num     = 1 if (self.onoff_char == "on") else 0
        self.pitch_num     = config.pitch_char2num_dicts[self.pitch_char]

    def num2char(self): ##numの状態をcharに反映させる
        self.dulation_char = config.dulation_num2char_dicts[self.dulation_num]
        self.onoff_char    = "on" if (self.onoff_num == 1) else "off"
        self.pitch_char    = config.pitch_num2char_dicts[self.pitch_num]
    
    
    def change_pitch(self,pentas_choice):        
        if self.onoff_char == "on":
            pitch_char = np.random.choice(list(config.pentas_choice.keys()),p=list(config.pentas_choice.values()),replace=True)
            self.pitch_char = pitch_char
        self.char2num()
                
class Bar:
    def __init__(self,beat=4):
        self.beat     = beat
        self.bar_reso = int( config.bar_reso * (self.beat/4) )
        self.notes    = []
        
    def append(self,note):
        self.notes.append(note)
    
class Motif: 
    def __init__(self,beat,bar_num,bpm):
        self.notes   = []
        self.beat     = beat
        self.bar_num  = bar_num #モチーフの小節数。
        
        self.bar_reso    = int( config.bar_reso * (self.beat/4) )
        self.motif_reso  = self.bar_reso * self.bar_num
        ###############仮置き###############
        self.bpm = bpm
        ###################################
        self.make_motif()
        
    def make_motif(self):#1小節リズム生成 
        motif_combination = np.random.choice(config.motif_pattern_list_text,p= config.motif_prob_list )
        np.random.shuffle( motif_combination )
        for note_char in motif_combination:
            onoff_char = np.random.choice(["on","off"], p=[0.9,0.1])
            note = Note(note_char,onoff_char,"C-2",bpm=self.bpm)
            note.change_pitch(pentas_choice = config.pentas_choice)
            self.notes.append(note)
            
        return self.notes
    
    def print_motif(self):
        for note in self.notes:
            print(note.dulation_char,note.pitch_char,note.onoff_char)
        
class Phrase: 
    def __init__(self,base_motif,part_name="Amelo",motif_patern="ABACABACABACABAC"):
        
        # 基本となるモチーフ
        self.base_motif   = base_motif 
        # Amelo,Bmelo,Sabi,etc..
        self.part_name     = part_name   
        self.motif_patern = motif_patern
        #phraseに含まれる小節数
        self.bar_num       = len(self.motif_patern) * self.base_motif.bar_num
        ##motifインスタンスのリスト
        self.motifs        = []
        
        self.motif_dict = self.make_motif_dict() 
        
        for patern in self.motif_patern:
            self.motifs.append( self.motif_dict[patern] )
            
    def make_motif_dict(self):
        unique_paterns = set(self.motif_patern)            
        motif_dict    = {}

        for patern in unique_paterns:
            motif_cp = copy.deepcopy(self.base_motif)
            
            if patern  == "A": #そのままコピー
                pass

            elif patern == "B": #リズムをキープしてピッチをふりなおす
                for note in motif_cp.notes:
                    note.change_pitch(pentas_choice=config.pentas_choice)

            elif patern == "C":  #完全新規
                motif_cp = Motif(beat=motif_cp.beat,bar_num=motif_cp.bar_num,bpm=motif_cp.bpm)
                
            motif_dict[patern] = motif_cp

        return motif_dict
    
    def print_phrase(self):
        for motief in self.motifs:
            print("---")
            motief.print_motif()
