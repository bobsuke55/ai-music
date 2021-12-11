いつうた



## 修正メモ

- ituuta  
  - make_musicxmlのmotifが1小節を前提としている。


##61 ～ 66が大分力技
  global melody_choice_list
  global melody_choice_prob_list 

  melody_choice_list       = utils.key_pentas_list(choice_key=self.KEY) 
  melody_choice_num        = len(melody_choice_list)
  melody_choice_prob_list  = [1/melody_choice_num for i in range(melody_choice_num)]
