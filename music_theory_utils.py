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

#数字が高い程、幅広いピッチレンジの曲が生成される確率が高くなる。
parts_prob_temature      =  {"Intro":1,"Amelo":1,"Bmelo":1,"Sabi":3}

#モチーフのリピートパターン 
#O:オリジナルモチーフ、(O)
#K:モチーフのリズムキープして、ピッチを降り直し(Keep)
#R:モチーフ再生成 (Rebuild)
#S{num}:Aモチーフのメロディラインをnum分上げる (Shift)
#F:third, fifth,rootで最後の音が終わる。(Fin)

all_motif_uniques        =  ["O","K","R","S","F"]
parts_phrase_patern_list = \
{   "Intro":[
           ["O","O","O","R","O","O","O","R"],
           ["O","O","K","R","O","O","K","R"],
           ["O","K","O","R","O","K","O","R"],
           ["O","K","K","R","O","K","K","R"]
        ],
 "Amelo":[
           ["O","O","O","R","O","O","O","R"],
           ["O","O","K","R","O","O","K","R"],
           ["O","K","O","R","O","K","O","R"],
           ["O","K","K","R","O","K","K","R"]
        ],
 "Bmelo":[ 
            ["O","S+1","S+2","R","O","S+1","S+2","R"], 
            ["O","S-1","S-2","R","O","S-1","S-2","R"],
        ],
 "Sabi":[
           ["O","O","O","F","O","O","O","F"],
           ["O","O","K","F","O","O","K","F"],
           ["O","K","O","F","O","K","O","F"],
           ["O","K","K","F","O","K","K","F"]
        ]
}

class ItsuUta:
    def __init__(self,name,NEUTRINO_PATH,genra="random"):

        self.songname       = name
        self.parts      = {"Intro":{"vocal_flg":False},
                           "Amelo":{"vocal_flg":True},
                           "Bmelo":{"vocal_flg":True},
                           "Sabi" :{"vocal_flg":True}}
                           #"Outro":{"vocal_flg":False}}

        self.BPM         = 0
        self.KEY         = "C"
        self.NEUTRINO    = NEUTRINO_PATH

        self.savepath = os.path.join("save",self.songname)
        os.makedirs(self.savepath,exist_ok=True)
        os.makedirs(os.path.join(self.savepath,"musicxml"),exist_ok=True)
        os.makedirs(os.path.join(self.savepath,"vocal"),exist_ok=True)

        self.select_loops(genra)

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
            #print(part,insts_dict)

    ### 自動作曲 ###
    def gen_music(self):
        for part_name,part_item in self.parts.items():

            phrase_pattern_list   = random.choice(parts_phrase_patern_list[part_name])
            base_phrase = Phrase(part_name=part_name,motif_patern=phrase_pattern_list,key=self.KEY,bpm=self.BPM)
            part_item["phrase"]= base_phrase
        
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
                print([self.NEUTRINO,musicxmlpath,part_name,outputpath])
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
    def __init__(self,part_name="Amelo",motif_patern=["A","B","A","C"],key="C",bpm=120):

        # Amelo,Bmelo,Sabi,etc..
        self.part_name     = part_name
        self.motif_patern  = motif_patern
        self.motif_uniques = set(self.motif_patern) # motif_patternに含まれるmotifリスト

        # メロディピッチの候補、キーにあったペンタトニックスケール。
        # recommended_range : きりたんの推奨音域にあったpitchだけTrue
        [self.choices_pitch_num,self.choices_pitch_char],self.key_penta_recommended_range = utils.key_pentas_list(key=key)

        self.BPM = bpm
        self.key = key

        ##motifインスタンスのリスト
        self.motifs      = []
        self.motif_dict  = self.make_motif_dict()

        for patern in self.motif_patern:
            self.motifs.append( copy.deepcopy( self.motif_dict[patern] ) )

    #モチーフを作成する。
    def create_motif(self,beat=4,bar_num=1):
        motif  = Motif(beat=beat,bar_num=bar_num,bpm=self.BPM)
        motif  = self.set_motif_pitch(motif=motif)
        return motif

    #motifのピッチをセットする。ピッチふりのメソッドはchoice_pitch_dis_prob(pre_pitchからの距離に応じたサンプル)
    def set_motif_pitch(self,motif,pre_pitch_char="N"):
        #pre_pitch_char = "N"ならモチーフの先頭ピッチがランダムに決まる。
        print("PIT",self.choices_pitch_char[self.key_penta_recommended_range])

        for note in motif.notes:
            if note.onoff_char == "off": #note offならskip
                continue
            if pre_pitch_char == "N": #先頭
                pitch_char = self.choice_pitch_random_uniform()
                
            else: #pre_pitch_charに基づいて決定
                pitch_char = self.choice_pitch_dis_prob(pre_pitch_char=pre_pitch_char,temp=parts_prob_temature[self.part_name])
                
            note.set_pitch(pitch_char=pitch_char)
            pre_pitch_char = pitch_char

        return motif

    def make_motif_dict(self): 

        motif_dict    = {} 

        #Original motifの作成
        motif_dict["O"] = self.create_motif(beat=4,bar_num=1)

        for motif_id in self.motif_uniques:
            if motif_id  == "O": #オリジナルは既にあるのでスキップ
                continue

            elif motif_id == "K": #K:モチーフのリズムキープして、ピッチを降り直し(Keep)
                motif = copy.deepcopy(motif_dict["O"])
                motif = self.set_motif_pitch(motif=motif,pre_pitch_char="N")

            elif motif_id == "R": #モチーフ再生成 (Regen)  
                motif = self.create_motif(beat=4,bar_num=1)
        
            elif "S" in motif_id: #S{num}:Originalモチーフのメロディラインをnum分shiftする (Shift)
                motif = copy.deepcopy(motif_dict["O"])
                pitch_shift = int(motif_id[1:])
                for note in motif.notes:
                    if note.onoff_char == "off":
                        continue
                    pitch_shift_ind  = np.where( self.choices_pitch_char == note.pitch_char )[0] + pitch_shift
                    pitch_shift_char = self.choices_pitch_char[pitch_shift_ind][0]
                    #print(pitch_shift_char)
                    note.set_pitch(pitch_shift_char)

            elif motif_id == "F": #モチーフ再生成かつthird, fifth,rootで最後の音が終わる。(Fin)
                motif = self.create_motif(beat=4,bar_num=1)

                third_char = config.pitch_num2char_dicts[config.pitch_char2num_dicts[f"{self.key}-2"] + 4][:-2]#third pitchを取得
                fifth_char = config.pitch_num2char_dicts[config.pitch_char2num_dicts[f"{self.key}-2"] + 7][:-2]#fifth pitchを取得

                root_ind   = np.array( [ i[:-2] == self.key for i in self.choices_pitch_char] )
                third_ind  = np.array( [ i[:-2] == third_char for i in self.choices_pitch_char] ) #third pitch の indを取得
                fifth_ind  = np.array( [ i[:-2] == fifth_char for i in self.choices_pitch_char] ) #fifth pitch の indを取得

                fin_choice_ind = self.key_penta_recommended_range & ( root_ind | third_ind | fifth_ind)
                
                pitch_char = random.choice( self.choices_pitch_char[fin_choice_ind] ) #推奨音域 & (third | fifth) の
                motif.last_on_note.set_pitch( pitch_char )
            
            else:
                assert 0,f"{motif_id} is not include in all_motif_uniques"
            
            motif_dict[motif_id] = motif

        return motif_dict
    
    def __dict__(self): #json に保存するため
        return {"motif_patern":"_".join(self.motif_patern)}

    def choice_pitch(self,pre_pitch="N"): ##いろいろな確率に基づいてnoteを決定する。
        if pre_pitch == "N": #直前のnoteがNなら
            pitch_char = self.choice_pitch_random_uniform()
        else:
            pitch_prob_std = self.pitch_dis_prob(pre_pitch,temp=1)

        return pitch_char

    def choice_pitch_dis_prob(self,pre_pitch_char,temp=1,power=1):
        #pre_pitchからの音の距離に応じて確率を決定。 
        #tempが大きいほど一様な確率になる。
        pre_pitch_num = config.pitch_char2num_dicts[pre_pitch_char]

        temp_choices_pitch_num  = self.choices_pitch_num[self.key_penta_recommended_range] 
        temp_choices_pitch_char = self.choices_pitch_char[self.key_penta_recommended_range] 

        pitch_abssub   = np.abs( temp_choices_pitch_num - pre_pitch_num )
        pitch_prob     = np.max( pitch_abssub ) - pitch_abssub + temp
        pitch_prob     = np.power(pitch_prob,power)
        pitch_prob     = pitch_prob/pitch_prob.sum()  #確率の正規化

        #確率に応じてサンプル
        pitch_char     = np.random.choice(temp_choices_pitch_char,p=pitch_prob)
        print(pitch_char,pitch_prob)

        """
        with open("test.txt","a") as f:
            prob_text = [ "{.2f}".format(i) for i in pitch_prob ]
            prob_text = pitch_char +":"+ "　".join(prob_text) + "\n"
            f.writelines(prob_text)
        """

        return pitch_char

    def choice_pitch_random_uniform(self): #一様確率でピッチを適当に選択
        pitch_char = random.choice(self.choices_pitch_char[self.key_penta_recommended_range])
        return pitch_char

    def print_phrase(self):
        for motief in self.motifs:
            print("---")
            motief.print_motif()

class Motif: 
    def __init__(self,beat,bpm,bar_num=bar_num):
        self.notes   = []
        self.beat     = beat
        self.bar_num  = bar_num #モチーフの小節数。
        self.last_on_note = None #あると便利なので、最後のon noteへの参照をもっておく
        
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
            note = Note(note_char,onoff_char,"N",bpm=self.bpm) #音程はNをセット
            #note.change_pitch(melody_choice_list=melody_choice_list,melody_choice_prob_list=melody_choice_prob_list)
            self.notes.append(note)

            if note.onoff_char == "on": #最後のon note への参照を持っておく。
                self.last_on_note = note

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
    
    def set_pitch(self,pitch_char):
        if self.onoff_char == "on":
            self.pitch_char = pitch_char    
            self.char2num()

        elif self.onoff_char == "off":
            assert 0, "これは休符です。"
