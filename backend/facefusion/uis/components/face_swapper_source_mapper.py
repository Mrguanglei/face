import json
from functools import partial
from typing import List, Optional

import cv2
import gradio
import numpy

from facefusion import logger, state_manager
from facefusion.localization import translator
from facefusion.jobs import job_store
from facefusion.face.face_analyser import get_many_faces
from facefusion.face.face_selector import sort_and_filter_faces
from facefusion.utils.filesystem import is_image, is_video
from facefusion.types import Face, VisionFrame
from facefusion.uis.core import get_ui_component, register_ui_component
from facefusion.media.vision import count_video_frame_total, fit_cover_frame, read_static_image, read_static_video_frame, read_video_frame

job_store.register_job_keys([ 'face_swapper_source_map' ])

MAX_FACE_COUNT = 8

DETECT_BUTTON : Optional[gradio.Button] = None
STATUS_TEXT : Optional[gradio.Textbox] = None

TARGET_PREVIEW_COMPONENTS : List[gradio.Image] = []
ARROW_MARKDOWN_COMPONENTS : List[gradio.Markdown] = []
SOURCE_IMAGE_COMPONENTS : List[gradio.Image] = []


def render() -> None:
	global DETECT_BUTTON, STATUS_TEXT
	global TARGET_PREVIEW_COMPONENTS, ARROW_MARKDOWN_COMPONENTS, SOURCE_IMAGE_COMPONENTS

	TARGET_PREVIEW_COMPONENTS = []
	ARROW_MARKDOWN_COMPONENTS = []
	SOURCE_IMAGE_COMPONENTS = []

	DETECT_BUTTON = gradio.Button(
		value = translator.get('uis.detect_target_faces_button') or '检测目标人脸',
		variant = 'primary'
	)
	STATUS_TEXT = gradio.Textbox(
		label = '状态',
		interactive = False,
		value = '请先上传目标文件，然后点击「检测目标人脸」'
	)

	for index in range(MAX_FACE_COUNT):
		with gradio.Row():
			with gradio.Column(scale = 2, min_width = 100):
				target_preview = gradio.Image(
					label = f'{translator.get("uis.target_face_label") or "目标人脸"} #{index + 1}',
					interactive = False,
					visible = False,
					height = 100,
					width = 100,
					container = False
				)
			with gradio.Column(scale = 1, min_width = 40):
				arrow = gradio.Markdown(
					value = '<div style="text-align:center; font-size:20px; color:#888; padding-top:35px;">➜</div>',
					visible = False
				)
			with gradio.Column(scale = 2, min_width = 100):
				source_image = gradio.Image(
					label = f'{translator.get("uis.source_face_label") or "替换为"} #{index + 1}',
					sources = [ 'upload' ],
					type = 'filepath',
					visible = False,
					height = 100,
					width = 100,
					container = False
				)
		TARGET_PREVIEW_COMPONENTS.append(target_preview)
		ARROW_MARKDOWN_COMPONENTS.append(arrow)
		SOURCE_IMAGE_COMPONENTS.append(source_image)

	register_ui_component('face_swapper_source_mapper_detect_button', DETECT_BUTTON)


def listen() -> None:
	all_outputs = [ STATUS_TEXT ]
	for index in range(MAX_FACE_COUNT):
		all_outputs.append(TARGET_PREVIEW_COMPONENTS[index])
		all_outputs.append(ARROW_MARKDOWN_COMPONENTS[index])
		all_outputs.append(SOURCE_IMAGE_COMPONENTS[index])

	DETECT_BUTTON.click(detect_target_faces, outputs = all_outputs)

	for index, source_image in enumerate(SOURCE_IMAGE_COMPONENTS):
		source_image.upload(
			partial(update_source_map, index),
			inputs = source_image,
			outputs = SOURCE_IMAGE_COMPONENTS[index]
		)

	target_file = get_ui_component('target_file')
	if target_file:
		for method in [ 'change', 'clear' ]:
			getattr(target_file, method)(clear_source_map, outputs = all_outputs)


def calculate_iou(box1, box2) -> float:
	"""计算两个 bounding box 的 IoU"""
	x1 = max(box1[0], box2[0])
	y1 = max(box1[1], box2[1])
	x2 = min(box1[2], box2[2])
	y2 = min(box1[3], box2[3])
	inter_area = max(0, x2 - x1) * max(0, y2 - y1)
	box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
	box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
	union_area = box1_area + box2_area - inter_area
	return inter_area / union_area if union_area > 0 else 0.0


def is_duplicate_face(new_face : Face, existing_faces : List[Face], iou_threshold : float = 0.3) -> bool:
	"""判断新检测到的人脸是否与已有列表中的人脸重复（基于 IoU）"""
	for existing_face in existing_faces:
		if calculate_iou(new_face.bounding_box, existing_face.bounding_box) > iou_threshold:
			return True
	return False


def detect_target_faces() -> List[gradio.components.Component]:
	try:
		target_path = state_manager.get_item('target_path')

		if not target_path:
			return build_outputs(0, [], message = '请先上传目标图片或视频')

		detected_faces : List[Tuple[Face, numpy.ndarray]] = []

		if is_image(target_path):
			vision_frame = read_static_image(target_path)
			if vision_frame is None:
				return build_outputs(0, [], message = '无法读取目标图片')
			faces = get_many_faces([vision_frame])
			faces = sort_and_filter_faces(faces)
			for face in faces:
				thumbnail = extract_face_thumbnail(vision_frame, face)
				detected_faces.append((face, thumbnail))

		elif is_video(target_path):
			frame_total = count_video_frame_total(target_path)
			if frame_total == 0:
				return build_outputs(0, [], message = '无法读取目标视频')

			# 均匀采样 15 帧（覆盖整段视频）
			sample_count = min(15, int(frame_total))
			sample_indices = [int(i * (frame_total - 1) / max(sample_count - 1, 1)) + 1 for i in range(sample_count)]

			for frame_number in sample_indices:
				vision_frame = read_video_frame(target_path, frame_number)
				if vision_frame is None:
					continue
				faces = get_many_faces([vision_frame])
				faces = sort_and_filter_faces(faces)
				for face in faces:
					if not is_duplicate_face(face, [f for f, _ in detected_faces]):
						thumbnail = extract_face_thumbnail(vision_frame, face)
						detected_faces.append((face, thumbnail))
		else:
			return build_outputs(0, [], message = '不支持的文件格式')

		face_count = min(len(detected_faces), MAX_FACE_COUNT)

		if face_count == 0:
			return build_outputs(0, [], message = '未检测到人脸')

		thumbnails = [t for _, t in detected_faces[:MAX_FACE_COUNT]]
		return build_outputs(face_count, thumbnails, message = f'检测到 {face_count} 张人脸，请为每张脸上传替换源图')

	except Exception as exception:
		logger.error(str(exception), __name__)
		return build_outputs(0, [], message = f'检测出错: {str(exception)}')


def build_outputs(face_count : int, thumbnails : List[numpy.ndarray], message : str) -> List[gradio.components.Component]:
	outputs : List[gradio.components.Component] = [ gradio.Textbox(value = message) ]

	for index in range(MAX_FACE_COUNT):
		if index < face_count and index < len(thumbnails):
			outputs.append(gradio.Image(value = thumbnails[index], visible = True))
			outputs.append(gradio.Markdown(value = '<div style="text-align:center; font-size:24px; color:#888; padding-top:50px;">➜</div>', visible = True))
			outputs.append(gradio.Image(value = None, visible = True, sources = [ 'upload' ], type = 'filepath'))
		else:
			outputs.append(gradio.Image(value = None, visible = False))
			outputs.append(gradio.Markdown(value = '', visible = False))
			outputs.append(gradio.Image(value = None, visible = False, sources = [ 'upload' ], type = 'filepath'))

	return outputs


def extract_face_thumbnail(vision_frame : VisionFrame, face : Face) -> numpy.ndarray:
	start_x, start_y, end_x, end_y = map(int, face.bounding_box)
	padding_x = int((end_x - start_x) * 0.25)
	padding_y = int((end_y - start_y) * 0.25)
	start_x = max(0, start_x - padding_x)
	start_y = max(0, start_y - padding_y)
	end_x = max(0, end_x + padding_x)
	end_y = max(0, end_y + padding_y)
	crop_vision_frame = vision_frame[start_y:end_y, start_x:end_x]
	crop_vision_frame = fit_cover_frame(crop_vision_frame, (128, 128))
	crop_vision_frame = cv2.cvtColor(crop_vision_frame, cv2.COLOR_BGR2RGB)
	return crop_vision_frame


def update_source_map(index : int, image_path) -> gradio.Image:
	logger.warn(f'[DEBUG] update_source_map index={index}, type={type(image_path)}, value={image_path}', __name__)

	source_map_str = state_manager.get_item('face_swapper_source_map') or '{}'

	try:
		source_map = json.loads(source_map_str)
	except Exception:
		source_map = {}

	file_path = None
	if image_path and isinstance(image_path, str):
		file_path = image_path
	elif image_path and hasattr(image_path, 'name'):
		file_path = image_path.name

	if file_path:
		source_map[str(int(index))] = file_path
	else:
		source_map.pop(str(int(index)), None)

	state_manager.set_item('face_swapper_source_map', json.dumps(source_map))

	if file_path:
		try:
			preview = read_static_image(file_path)
			preview = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
			logger.warn(f'[DEBUG] loaded preview shape={preview.shape}', __name__)
			return gradio.Image(value = preview, visible = True, sources = [ 'upload' ], type = 'filepath', height = 100, width = 100, container = False)
		except Exception as exception:
			logger.warn(f'[DEBUG] failed to load preview: {exception}', __name__)
	return gradio.Image(value = None, visible = True, sources = [ 'upload' ], type = 'filepath', height = 100, width = 100, container = False)


def clear_source_map(_ = None) -> List[gradio.components.Component]:
	state_manager.set_item('face_swapper_source_map', '{}')
	return build_outputs(0, [], message = '请先上传目标文件，然后点击「检测目标人脸」')
