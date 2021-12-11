import numpy as np
import itertools
import copy
import config
import utils
import subprocess
import random
import os
import glob
import music21 as m2
from pydub import AudioSegment
import soundfile as sf
import pickle as pkl
import json

# For Note Class
## Noteの生成音の候補と確率 # 全て等確率とする。きりたんの音域は、B3 ～ D5
#melody_choice_list       = utils.key_pentas_list(choice_key="C") #
#melody_choice_num        = len(melody_choice_list)
#melody_choice_prob_list  = [1/melody_choice_num for i in range(melody_choice_num)]

# For Motif Class
# melody には以下の音符しか現れない。
use_note_lists = ["bar","half","quarter","dotted_quarter","quaver"]
#motif_pattern_一覧
motif_pattern_list,motif_pattern_prob_list = utils.make_motif_pattern_list(use_note_lists) 
#use_note_lists = ["bar","half","quarter","dotted_quarter","quaver","dotted_quaver","quarter_tri","quaver_tri","semiquaver"]

#note on と offの確率
onoff_prob_list = [0.9,0.1]

#For Phrase class
beat    = 4
bar_num = 1

#モチーフのリピートパターン A:そのままモチーフ、B:音程降り直し、C:モチーフつくりなおし
phrase_choice_list       =  ["AAACAAAC","AABCAABC","ABACABAC","ABBCABBC"]
phrase_choice_num        =  len(phrase_choice_list)
phrase_choice_prob_list  =  [1/phrase_choice_num for i in range(phrase_choice_num)]


class ItsuUta:
    def __init__(self,name,genra="random"):

        self.songname       = name
        self.parts      = {"Intro":{"vocal_flg":False},
                           "Amelo":{"vocal_flg":True},
                           "Bmelo":{"vocal_flg":True},
                           "Sabi" :{"vocal_flg":True}}
                           #"Outro":{"vocal_flg":False}}

        self.BPM         = 0
        self.KEY         = "C"
        self.NEUTRINO    = "C:\\Users\\yusuke\\Desktop\\Music\\NEUTRINO-Windows_v0.500\\Run_arg.bat"

        self.savepath = os.path.join("save",self.songname)
        os.makedirs(self.savepath,exist_ok=True)
        os.makedirs(os.path.join(self.savepath,"musicxml"),exist_ok=True)
        os.makedirs(os.path.join(self.savepath,"vocal"),exist_ok=True)

        self.select_loops(genra)

        global melody_choice_list
        global melody_choice_prob_list 

        melody_choice_list       = utils.key_pentas_list(choice_key=self.KEY) 
        melody_choice_num        = len(melody_choice_list)
        melody_choice_prob_list  = [1/melody_choice_num for i in range(melody_choice_num)]

    def select_loops(self,genra=None):
        genras = os.listdir(f"loop8m\\")
        if genra is "random":
            genra  = random.choice(genras)

        bpm_keys = os.listdir(f"loop8m\\{genra}\\")
        bpm_key  = random.choice(bpm_keys)

        #bpmとkeyを取得
        self.BPM = int( bpm_key.split("-")[0])
        self.KEY = bpm_key.split("-")[1]
        print(self.BPM,self.KEY)

        parts = os.listdir(f"loop8m\\{genra}\\{bpm_key}")
        for part in parts:
            insts = os.listdir(f"loop8m\\{genra}\\{bpm_key}\\{part}")
            insts_dict = {}
            for inst in insts:
                loops = glob.glob(f"loop8m\\{genra}\\{bpm_key}\\{part}\\{inst}\\*.wav")
                loop  = random.choice(loops)
                insts_dict[inst] = loop
            self.parts[part]["loops"] = insts_dict
            print(part,insts_dict)

    ### 自動作曲 ###
    def gen_music(self):
        for part in self.parts:
            base_motif  = Motif(beat=4,bar_num=1,bpm=self.BPM)
            motif_str   = np.random.choice(phrase_choice_list,p=phrase_choice_prob_list)
            base_phrase = Phrase(base_motif=base_motif,part_name=part,motif_patern=motif_str)
            self.parts[part]["phrase"]= base_phrase
        
    ### 歌詞をNoteにセットする。
    def set_lyric(self,set_lyric="あいうえお",setmode="repeat"):
        #setmodeが"repeat"の場合、各partごとで歌詞をリピートする。
        lyric_ind = 0
        lyric_len = len(set_lyric)

        for part_name,part_item in self.parts.items():
            if not part_item["vocal_flg"]:
                continue

            if setmode == "repeat":
                lyric_ind = 0

            phrase = part_item["phrase"]
            for motif in phrase.motifs:
                for note in motif.notes:
                    if note.onoff_char == "on":                        
                        note.lyric = set_lyric[lyric_ind%lyric_len]
                        lyric_ind += 1

    #music_xmlの準備
    def make_musicxml(self,pitch_bias=-12): 
        for part_name,part_item in self.parts.items():
            phrase = part_item["phrase"]

            myinst = m2.instrument.Instrument()
            myinst.partName = part_name

            mystrm = m2.stream.Part()
            mystrm.append(myinst)
            mystrm.append(m2.key.Key('c', 'major'))
            mystrm.append(m2.clef.TrebleClef())

            #空の1小節を先頭に入れる

            cur_measure = m2.stream.Measure()
            cur_measure.append( m2.tempo.MetronomeMark(number=self.BPM) ) 
            mystrm.append(cur_measure)

            for motif in phrase.motifs:
                cur_measure = m2.stream.Measure() 
                cur_measure.append( m2.tempo.MetronomeMark(number=self.BPM) ) 
                
                for note in motif.notes:
                    quater_length = note.dulation_num/config.quarter_reso

                    if note.onoff_char == "on":
                        note_number = note.pitch_num + pitch_bias
                        n = m2.note.Note(note_number, quarterLength=quater_length, lyric=note.lyric)

                    elif note.onoff_char == "off":
                        n = m2.note.Rest(quarterLength=quater_length)

                    else:
                        assert 0, "note.onoff_char is on or off"
                
                    cur_measure.append(n)
                mystrm.append(cur_measure)

            #空の小節を後ろに入れる。
            cur_measure = m2.stream.Measure() 
            cur_measure.append( m2.tempo.MetronomeMark(number=self.BPM) ) 
            mystrm.append(cur_measure)

            path_musicxmls = os.path.join(os.path.join(self.savepath,"musicxml"),f"{part_name}.musicxml")
            mystrm.write(fp=path_musicxmls)
            self.parts[part_name]["musicxml"]= os.path.abspath(path_musicxmls)

    #musicxml => NEUTRINO => wav 
    def synth_vocal(self):

        proc_list = []
        for part_name,part_item in self.parts.items():
        
            musicxmlpath = part_item["musicxml"]
            outputpath   = os.path.join(os.path.join(self.savepath,"vocal"),f"{part_name}.wav")
            outputpath   = os.path.abspath(outputpath)
            part_item["vocal_synth"] = outputpath

            if part_item["vocal_flg"]:
                proc = subprocess.Popen([self.NEUTRINO,musicxmlpath,part_name,outputpath])
                proc_list.append(proc)
            else:#便宜上空のwavファイルを作成する。
                ####ハードコーディングになってる
                data = np.zeros([int( 48000*60/self.BPM * 4 * config.bar_num )]) 
                sf.write(outputpath,data,48000)

        for subproc in proc_list:
            subproc.wait()
        
        print("fin synthesis")

    def preprocess_vocal(self):
        ##合成した歌声に加工をあてる、前後の1小節を消すとか。
        for part_name,part_item in self.parts.items():
            if part_item["vocal_flg"]:
                utils.cut_firstend_bar(wav_path=part_item["vocal_synth"],bpm=self.BPM)

    def preprocess_loop(self):
        pass
        
    def compose(self,inst_gain=-8):
        part_compose_list = []
        part_samplerate_list = []

        for part_name,part_item in self.parts.items():
            compose_path = os.path.join(self.savepath,"compose")
            os.makedirs(compose_path,exist_ok=True)

            #intro outro は空のwavファイルを読む。
            output = AudioSegment.from_file(part_item["vocal_synth"])
            for loop in part_item["loops"].values():
                sound  = AudioSegment.from_file(loop) + inst_gain
                output = output.overlay(sound,position=0)

            part_compose_path = os.path.join(compose_path,f"{part_name}.wav")
            output.export(part_compose_path, format="wav")

            data,samplerate = sf.read(part_compose_path)
            part_compose_list.append(data)
            part_samplerate_list.append(samplerate)

        part_compose_list.append(part_compose_list[0]) #outro = intro
        assert all(val == part_samplerate_list[0] for val in part_samplerate_list)
        all_song = np.concatenate(part_compose_list,axis=0)
        sf.write(os.path.join(compose_path,"Song.wav"),all_song,part_samplerate_list[0])

    def print_part(self):
        for part_name,part_item in self.parts.items():
            print(part_name,"="*20)
            phrase = part_item["phrase"]
            for motif in phrase.motifs:
                motif.print_motif()

    def save_instance(self):

        instance_path = os.path.join(self.savepath,"itsuuta.pkl")
        with open(instance_path,"wb") as f:
            pkl.dump(self,f)

        json_path = os.path.join(self.savepath,"itsuuta.json")
        json_file = open(json_path,"w")
        json.dump(self.parts,json_file,default=default_method,indent=2)

def default_method(item):
    if isinstance(item, object) and hasattr(item, '__dict__'):
        return item.__dict__
    else:
        raise TypeError

class Phrase: 
    def __init__(self,base_motif,part_name="Amelo",motif_patern="ABAC"):
        
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
            self.motifs.append( copy.deepcopy( self.motif_dict[patern] ) )

    def __dict__(self): #json に保存するため
        return self.part_name

    def make_motif_dict(self):
        unique_paterns = set(self.motif_patern)
        motif_dict    = {}

        for patern in unique_paterns:
            motif_cp = copy.deepcopy(self.base_motif)
            
            if patern  == "A": #そのままコピー
                pass

            elif patern == "B": #リズムをキープしてピッチをふりなおす
                for note in motif_cp.notes:
                    note.change_pitch( melody_choice_list = melody_choice_list,melody_choice_prob_list=melody_choice_prob_list)

            elif patern == "C":  #完全新規
                motif_cp = Motif(beat=motif_cp.beat,bar_num=motif_cp.bar_num,bpm=motif_cp.bpm)
                
            motif_dict[patern] = motif_cp

        return motif_dict
    
    def print_phrase(self):
        for motief in self.motifs:
            print("---")
            motief.print_motif()

    
class Motif: 
    def __init__(self,beat,bpm,bar_num=bar_num):
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
        motif_combination = np.random.choice(motif_pattern_list,p=motif_pattern_prob_list )
        np.random.shuffle( motif_combination )
        for note_char in motif_combination:
            onoff_char = np.random.choice(["on","off"], p=onoff_prob_list)
            note = Note(note_char,onoff_char,"C-2",bpm=self.bpm)
            note.change_pitch(melody_choice_list=melody_choice_list,melody_choice_prob_list=melody_choice_prob_list)
            self.notes.append(note)
            
        return self.notes
    
    def print_motif(self):
        print(f"{bar_num}bar-----")
        for note in self.notes:
            print(note)

class Bar:
    def __init__(self,beat=4):
        self.beat     = beat
        self.bar_reso = int( config.bar_reso * (self.beat/4) )
        self.notes    = []
        
    def append(self,note):
        self.notes.append(note)

#音符
class Note:
    def __init__(self,dulation_char,onoff_char,pitch_char="C-2",bpm=config.tempo):
        self.dulation_char  = dulation_char # quaver, (長さ) "quaver"
        self.onoff_char     = onoff_char # on or off 
        self.pitch_char     = pitch_char #'C5'
        self.bpm            = bpm
        self.lyric          = ""
        self.char2num()

    def __repr__(self):
        return f"{self.pitch_char}:{self.dulation_char}:{self.onoff_char}:{self.lyric}"
        
    def char2num(self): ##charの状態をnumに反映させる
        self.dulation_num  = config.dulation_char2num_dicts[self.dulation_char]
        self.onoff_num     = 1 if (self.onoff_char == "on") else 0
        self.pitch_num     = config.pitch_char2num_dicts[self.pitch_char]

    def num2char(self): ##numの状態をcharに反映させる
        self.dulation_char = config.dulation_num2char_dicts[self.dulation_num]
        self.onoff_char    = "on" if (self.onoff_num == 1) else "off"
        self.pitch_char    = config.pitch_num2char_dicts[self.pitch_num]
    
    def change_pitch(self,melody_choice_list,melody_choice_prob_list):
        if self.onoff_char == "on":
            pitch_char = np.random.choice(melody_choice_list,p=melody_choice_prob_list,replace=True)
            self.pitch_char = pitch_char
        self.char2num()
    



