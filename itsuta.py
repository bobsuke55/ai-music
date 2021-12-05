import pretty_midi
import numpy as np
from music_theory_utils import Motif,Phrase
import datetime
import copy
import itertools
import os
import shutil
import glob
import wave
import struct
from scipy import fromstring, int16
import music21 as m2
import random
from pydub import AudioSegment

def cut_first_bar(wavf,BPM):
    wr = wave.open(wavf, 'r')
    ch = wr.getnchannels()
    width = wr.getsampwidth()
    fr = wr.getframerate()
    fn = wr.getnframes()

    data = wr.readframes(wr.getnframes())
    wr.close()
    X = fromstring(data, dtype=int16)

    bar_frames = int(fr*240/BPM)

    Y = X[bar_frames:-bar_frames]
    outd = struct.pack("h" * len(Y), *Y)

    # 書き出し
    ww = wave.open(wavf, 'w')
    ww.setnchannels(ch)
    ww.setsampwidth(width)
    ww.setframerate(fr)
    ww.writeframes(outd)
    ww.close()

VERSION_NUM = "17"
#ループ素材決定
loop_lists = glob.glob("./loop/*.wav")
loop_wav   = random.choice(loop_lists)
#####ハードコーディング############
BPM = int( loop_wav[loop_wav.find("bpm")+3:].replace(".wav",""))

#変数名を考えたい
motif_list = ["AAACAAAC","AABCAABC","ABACABAC","ABBCABBC"]
motif_str   = random.choice(motif_list)

#歌詞、BPM
with open("lyric.txt","r",encoding="utf-8") as f:
    lyric_list = f.readlines()

INPUT_LYRIC = random.choice(lyric_list).replace("\n","")
print(INPUT_LYRIC)

##固定
MUSICXML_PATH = "C:/Users/yusuke/Desktop/Music/NEUTRINO-Windows_v0.500/score/musicxml/test.xml" 
NEUTRINO_OUTPUT_PATH  = "C:/Users/yusuke/Desktop/Music/NEUTRINO-Windows_v0.500/output/test_syn.wav" 

NEUTRINO_OUTPUT_BASEPATH = "C:/Users/yusuke/Desktop/Projects/ai-music/neutrino_file_store"
NEUTRINO_RUN = "C:/Users/yusuke/Desktop/Music/NEUTRINO-Windows_v0.500/Run.bat"

### 自動作曲 ###
base_motif  = Motif(beat=4,bar_num=1,bpm=BPM)
base_phrase = Phrase(base_motif=base_motif,part_name="Amelo",motif_patern=motif_str)
lyric       = [i for i in INPUT_LYRIC]
len_lyric   = len(lyric)

### 曲 + 歌詞でmusicxml生成 ###
mystrm = m2.stream.Part()
myinst = m2.instrument.Instrument()
myinst.partName = "Kiritan"
mystrm.append(myinst)
mystrm.append(m2.key.Key('c', 'major'))
mystrm.append(m2.clef.TrebleClef())

ind_lyric  = 0
pitch_bias = -12

for motif in base_phrase.motifs: # 8小節
    cur_measure = m2.stream.Measure() 
    cur_measure.append( m2.tempo.MetronomeMark(number=motif.notes[0].bpm) ) 
    for note in motif.notes:
        quater_length = note.dulation_num/24
        #print(note.dulation_char,note.pitch_char,note.onoff_char)
        #print(note.dulation_num,note.pitch_num,note.onoff_num)

        if note.onoff_char == "on":
            note_number = note.pitch_num + pitch_bias
            char = lyric[ind_lyric%len_lyric]
            ind_lyric += 1
            n = m2.note.Note(note_number, quarterLength=quater_length, lyric=char)

        else:# 休符
            n = m2.note.Rest(quarterLength=quater_length)
            # 音符を放り込んだ小節をストリームに放り込む
        cur_measure.append(n)
    mystrm.append(cur_measure)

mystrm.write(fp=MUSICXML_PATH)

### neurtrinoにmusicxmlを入力して、きりたん生成
import subprocess

returncode = subprocess.call(NEUTRINO_RUN, shell=True)

##はじめと終わりの一小節を除去
cut_first_bar(NEUTRINO_OUTPUT_PATH,BPM=BPM)

##曲の保存
dt_now = datetime.datetime.now()

if os.path.exists(MUSICXML_PATH):
    copy_musicxml = NEUTRINO_OUTPUT_BASEPATH + f'/{VERSION_NUM}_{dt_now.year:04d}{dt_now.month:02d}{dt_now.day:02d}_{dt_now.hour:02d}{dt_now.minute:02d}{dt_now.second:02d}.musicxml'
    shutil.copyfile(MUSICXML_PATH, copy_musicxml)
else:
    print("musicxmlファイルのコピーに失敗しました")

if os.path.exists(NEUTRINO_OUTPUT_PATH):
    copy_wav = NEUTRINO_OUTPUT_BASEPATH + f'/{VERSION_NUM}_{dt_now.year:04d}{dt_now.month:02d}{dt_now.day:02d}_{dt_now.hour:02d}{dt_now.minute:02d}{dt_now.second:02d}.wav'
    shutil.copyfile(NEUTRINO_OUTPUT_PATH, copy_wav)
else:
    print("wavファイルのコピーに失敗しました")


##loop音源との組み合わせ
sound1 = AudioSegment.from_file(NEUTRINO_OUTPUT_PATH)
sound2 = AudioSegment.from_file(loop_wav)
output = sound1.overlay(sound2, position=0)

#これも汚い
loop_name = os.path.basename(loop_wav)
output.export(copy_wav.replace(".wav","")+loop_name, format="wav")