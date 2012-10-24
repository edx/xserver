#Defines an essay set object, which encapsulates essays from training and test sets.
#Performs spell and grammar checking, tokenization, and stemming.

import numpy
import nltk
import sys
import random
import os

base_path = os.path.dirname(__file__)
sys.path.append(base_path)
import util_functions


class essay_set:
    
    def __init__(self, type="train"):
        if(type!="train" and type!="test"):
            type="train"
        self._type = type
        self._score,self._text,self._id,self._clean_text,self._tokens,self._pos,\
        self._clean_stem_text,self._generated=[],[],[],[],[],[],[],[]
        self._prompt=""
    
    def add_essay(self,essay_text,essay_score,essay_generated=0):
        if(len(self._id)>0):
            max_id=max(self._id)
        else :
            max_id=0
        if type(essay_score)==type(0) and type(essay_text)==type("text") and type(essay_generated)==type(0) \
           and (essay_generated==0 or essay_generated==1):
            self._id.append(max_id+1)
            self._score.append(essay_score)
            self._text.append(util_functions.sub_chars(essay_text).lower())
            self._clean_text.append(util_functions.spell_correct(self._text[len(self._text)-1]))
            self._tokens.append(nltk.word_tokenize(self._clean_text[len(self._clean_text)-1]))
            self._pos.append(nltk.pos_tag(self._tokens[len(self._tokens)-1]))
            self._generated.append(essay_generated)
            porter = nltk.PorterStemmer()
            por_toks=" ".join([porter.stem(w) for w in self._tokens[len(self._tokens)-1]])
            self._clean_stem_text.append(por_toks)
            ret="text: " + self._text[len(self._text)-1] + " score: " + str(essay_score)
        else:
            raise util_functions.InputError(essay_text,"arguments need to be in format (text,score). "
                                                       "text needs to be string, score needs to be int.")
        return ret
        
    def update_prompt(self,prompt_text):
        if(type(prompt_text)==type("text")):
            self._prompt=util_functions.sub_chars(prompt_text)
            ret=self._prompt
        else:
            raise util_functions.InputError(prompt_text,"Invalid prompt. Need to enter a string value.")
        return ret
        
        
    def generate_additional_essays(self,e_text,e_score,dict=None,max_syns=3):
        random.seed(1)
        e_toks=nltk.word_tokenize(e_text)
        all_syns=[]
        for word in e_toks:
            synonyms=util_functions.get_wordnet_syns(word)
            if(len(synonyms)>max_syns):
                synonyms=random.sample(synonyms,max_syns)
            all_syns.append(synonyms)
        new_essays=[]
        for i in range(0,max_syns):
            syn_toks=e_toks
            for z in range(0,len(e_toks)):
                if len(all_syns[z])>i and (dict==None or e_toks[z] in dict):
                    syn_toks[z]=all_syns[z][i]
            new_essays.append(" ".join(syn_toks))
        for z in xrange(0,len(new_essays)):
            self.add_essay(new_essays[z],e_score,1)