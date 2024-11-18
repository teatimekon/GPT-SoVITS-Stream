'''
按中英混合识别
按日英混合识别
多语种启动切分识别语种
全部按中文识别
全部按英文识别
全部按日文识别
'''
import logging
import traceback
import pdb
import torch



import gradio as gr
from transformers import AutoModelForMaskedLM, AutoTokenizer
import numpy as np
import librosa
from feature_extractor import cnhubert

from module.models import SynthesizerTrn
from AR.models.t2s_lightning_module import Text2SemanticLightningModule
from text import cleaned_text_to_sequence
from text.cleaner import clean_text
from time import time as ttime
from module.mel_processing import spectrogram_torch
from tools.my_utils import load_audio
from tools.i18n.i18n import I18nAuto, scan_language_list

from text import chinese

import logging
import traceback

import LangSegment, os, re, sys, json

try:
    import gradio.analytics as analytics
    analytics.version_check = lambda:None
except:...

def my_test():
    return 'hello'