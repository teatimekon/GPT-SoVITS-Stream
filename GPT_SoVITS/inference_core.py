
import time, os, json, sys, re
import torch

from pyinstrument import Profiler

profiler = Profiler()
profiler.start()


load_model_start_time = time.perf_counter()

version=os.environ.get("version","v2")
pretrained_sovits_name=["GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s2G2333k.pth", "GPT_SoVITS/pretrained_models/s2G488k.pth"]
pretrained_gpt_name=["GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt", "GPT_SoVITS/pretrained_models/s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt"]

_ =[[],[]]
for i in range(2):
    if os.path.exists(pretrained_gpt_name[i]):
        _[0].append(pretrained_gpt_name[i])
    if os.path.exists(pretrained_sovits_name[i]):
        _[-1].append(pretrained_sovits_name[i])
pretrained_gpt_name,pretrained_sovits_name = _


if os.path.exists(f"./weight.json"):
    pass
else:
    with open(f"./weight.json", 'w', encoding="utf-8") as file:json.dump({'GPT':{},'SoVITS':{}},file)

with open(f"./weight.json", 'r', encoding="utf-8") as file:
    weight_data = file.read()
    weight_data=json.loads(weight_data)
    gpt_path = os.environ.get(
        "gpt_path", weight_data.get('GPT',{}).get(version,pretrained_gpt_name))
    sovits_path = os.environ.get(
        "sovits_path", weight_data.get('SoVITS',{}).get(version,pretrained_sovits_name))
    if isinstance(gpt_path,list):
        gpt_path = gpt_path[0]
    if isinstance(sovits_path,list):
        sovits_path = sovits_path[0]

# gpt_path = os.environ.get(
#     "gpt_path", pretrained_gpt_name
# )
# sovits_path = os.environ.get("sovits_path", pretrained_sovits_name)
cnhubert_base_path = os.environ.get(
    "cnhubert_base_path", "GPT_SoVITS/pretrained_models/chinese-hubert-base"
)
bert_path = os.environ.get(
    "bert_path", "GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large"
)
infer_ttswebui = os.environ.get("infer_ttswebui", 9872)
infer_ttswebui = int(infer_ttswebui)
is_share = os.environ.get("is_share", "False")
is_share = eval(is_share)
if "_CUDA_VISIBLE_DEVICES" in os.environ:
    os.environ["CUDA_VISIBLE_DEVICES"] = os.environ["_CUDA_VISIBLE_DEVICES"]
is_half = eval(os.environ.get("is_half", "True")) and torch.cuda.is_available()
punctuation = set(['!', '?', '…', ',', '.', '-'," "])


# import gradio as gr
from transformers import AutoModelForMaskedLM, AutoTokenizer
import numpy as np
# import librosa
from feature_extractor import cnhubert

cnhubert.cnhubert_base_path = cnhubert_base_path

from module.models import SynthesizerTrn
from AR.models.t2s_lightning_module import Text2SemanticLightningModule
from text import cleaned_text_to_sequence
from text.cleaner import clean_text
from time import time as ttime
from module.mel_processing import spectrogram_torch
# from tools.my_utils import load_audio
# from tools.i18n.i18n import I18nAuto, scan_language_list

language=os.environ.get("language","Auto")
# language=sys.argv[-1] if sys.argv[-1] in scan_language_list() else language
# i18n = I18nAuto(language=language)

# os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'  # 确保直接启动推理UI时也能够设置。

if torch.cuda.is_available():
    device = "cuda"
else:
    device = "cpu"

# dict_language_v1 = {
#     i18n("中文"): "all_zh",#全部按中文识别
#     i18n("英文"): "en",#全部按英文识别#######不变
#     i18n("日文"): "all_ja",#全部按日文识别
#     i18n("中英混合"): "zh",#按中英混合识别####不变
#     i18n("日英混合"): "ja",#按日英混合识别####不变
#     i18n("多语种混合"): "auto",#多语种启动切分识别语种
# }
# dict_language_v2 = {
#     i18n("中文"): "all_zh",#全部按中文识别
#     i18n("英文"): "en",#全部按英文识别#######不变
#     i18n("日文"): "all_ja",#全部按日文识别
#     i18n("粤语"): "all_yue",#全部按中文识别
#     i18n("韩文"): "all_ko",#全部按韩文识别
#     i18n("中英混合"): "zh",#按中英混合识别####不变
#     i18n("日英混合"): "ja",#按日英混合识别####不变
#     i18n("粤英混合"): "yue",#按粤英混合识别####不变
#     i18n("韩英混合"): "ko",#按韩英混合识别####不变
#     i18n("多语种混合"): "auto",#多语种启动切分识别语种
#     i18n("多语种混合(粤语)"): "auto_yue",#多语种启动切分识别语种
# }
# dict_language = dict_language_v1 if version =='v1' else dict_language_v2

tokenizer = AutoTokenizer.from_pretrained(bert_path)
bert_model = AutoModelForMaskedLM.from_pretrained(bert_path)
if is_half == True:
    bert_model = bert_model.half().to(device)
else:
    bert_model = bert_model.to(device)

load_model_end_time = time.perf_counter()
print("TTS webui load model cost time: {}s".format( load_model_end_time - load_model_start_time))


# @timethis
def get_bert_feature(text, word2ph):
    with torch.no_grad():
        inputs = tokenizer(text, return_tensors="pt")
        for i in inputs:
            inputs[i] = inputs[i].to(device)
        res = bert_model(**inputs, output_hidden_states=True)
        res = torch.cat(res["hidden_states"][-3:-2], -1)[0].cpu()[1:-1]
    assert len(word2ph) == len(text)
    phone_level_feature = []
    for i in range(len(word2ph)):
        repeat_feature = res[i].repeat(word2ph[i], 1)
        phone_level_feature.append(repeat_feature)
    phone_level_feature = torch.cat(phone_level_feature, dim=0)
    return phone_level_feature.T


class DictToAttrRecursive(dict):
    def __init__(self, input_dict):
        super().__init__(input_dict)
        for key, value in input_dict.items():
            if isinstance(value, dict):
                value = DictToAttrRecursive(value)
            self[key] = value
            setattr(self, key, value)

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError(f"Attribute {item} not found")

    def __setattr__(self, key, value):
        if isinstance(value, dict):
            value = DictToAttrRecursive(value)
        super(DictToAttrRecursive, self).__setitem__(key, value)
        super().__setattr__(key, value)

    def __delattr__(self, item):
        try:
            del self[item]
        except KeyError:
            raise AttributeError(f"Attribute {item} not found")

ssl_model_start_time = time.perf_counter()
ssl_model = cnhubert.get_model()
if is_half == True:
    ssl_model = ssl_model.half().to(device)
else:
    ssl_model = ssl_model.to(device)

ssl_model_end_time = time.perf_counter()
print("get ssl_model cost time: {}s".format(ssl_model_end_time - ssl_model_start_time))


profiler.stop()
profiler.print()