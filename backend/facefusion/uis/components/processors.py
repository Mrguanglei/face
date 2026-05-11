from typing import List, Optional

import gradio

from facefusion import state_manager
from facefusion.localization import translator
from facefusion.utils.filesystem import get_file_name, resolve_file_paths
from facefusion.processors.core import get_processors_modules
from facefusion.uis.core import register_ui_component

PROCESSORS_CHECKBOX_GROUP : Optional[gradio.CheckboxGroup] = None

PROCESSOR_LABELS =\
{
	'face_swapper': '换脸',
	'age_modifier': '年龄修改',
	'background_remover': '背景移除',
	'deep_swapper': '深度换脸',
	'expression_restorer': '表情恢复',
	'face_debugger': '人脸调试',
	'face_editor': '人脸编辑',
	'face_enhancer': '人脸增强',
	'frame_colorizer': '帧上色',
	'frame_enhancer': '帧增强',
	'lip_syncer': '唇形同步'
}


def render() -> None:
	global PROCESSORS_CHECKBOX_GROUP

	PROCESSORS_CHECKBOX_GROUP = gradio.CheckboxGroup(
		label = translator.get('uis.processors_checkbox_group'),
		choices = sort_processors(state_manager.get_item('processors')),
		value = state_manager.get_item('processors')
	)
	register_ui_component('processors_checkbox_group', PROCESSORS_CHECKBOX_GROUP)


def listen() -> None:
	PROCESSORS_CHECKBOX_GROUP.change(update_processors, inputs = PROCESSORS_CHECKBOX_GROUP, outputs = PROCESSORS_CHECKBOX_GROUP)


def update_processors(processors : List[str]) -> gradio.CheckboxGroup:
	for processor_module in get_processors_modules(state_manager.get_item('processors')):
		if hasattr(processor_module, 'clear_inference_pool'):
			processor_module.clear_inference_pool()

	for processor_module in get_processors_modules(processors):
		if not processor_module.pre_check():
			return gradio.CheckboxGroup()

	state_manager.set_item('processors', processors)
	return gradio.CheckboxGroup(value = state_manager.get_item('processors'), choices = sort_processors(state_manager.get_item('processors')))


def sort_processors(processors : List[str]) -> List[dict]:
	available_processors = [ get_file_name(file_path) for file_path in resolve_file_paths('facefusion/processors/modules') ]
	current_processors = []

	for processor in processors + available_processors:
		if processor in available_processors and processor not in current_processors:
			current_processors.append(processor)

	return [ (PROCESSOR_LABELS.get(processor, processor), processor) for processor in current_processors ]
