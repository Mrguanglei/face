import base64
import io
import json
import os
import time
from typing import List, Tuple

import cv2
import numpy
from fastapi import APIRouter, UploadFile, File, WebSocket
from fastapi.responses import FileResponse, JSONResponse

from facefusion import logger, state_manager
from facefusion.face.face_analyser import get_many_faces
from facefusion.face.face_selector import sort_and_filter_faces
from facefusion.utils.filesystem import is_image, is_video, resolve_relative_path
from facefusion.types import Face, VisionFrame
from facefusion.media.vision import count_video_frame_total, fit_cover_frame, read_static_image, read_video_frame

router = APIRouter(prefix = '/api')

UPLOAD_DIR = resolve_relative_path('uploads')
THUMB_DIR = os.path.join(UPLOAD_DIR, 'thumbnails')
os.makedirs(UPLOAD_DIR, exist_ok = True)
os.makedirs(THUMB_DIR, exist_ok = True)


def calculate_iou(box1, box2) -> float:
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
	for existing_face in existing_faces:
		if calculate_iou(new_face.bounding_box, existing_face.bounding_box) > iou_threshold:
			return True
	return False


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


def detect_faces_from_target() -> dict:
	target_path = state_manager.get_item('target_path')
	if not target_path:
		return {'success': False, 'message': '请先上传目标文件'}

	all_faces : List[Tuple[Face, numpy.ndarray]] = []

	if is_image(target_path):
		vision_frame = read_static_image(target_path)
		if vision_frame is None:
			return {'success': False, 'message': '无法读取目标图片'}
		faces = get_many_faces([vision_frame])
		faces = sort_and_filter_faces(faces)
		for face in faces:
			thumbnail = extract_face_thumbnail(vision_frame, face)
			all_faces.append((face, thumbnail))

	elif is_video(target_path):
		frame_total = count_video_frame_total(target_path)
		if frame_total == 0:
			return {'success': False, 'message': '无法读取目标视频'}

		sample_count = min(15, int(frame_total))
		sample_indices = [int(i * (frame_total - 1) / max(sample_count - 1, 1)) + 1 for i in range(sample_count)]

		for frame_number in sample_indices:
			vision_frame = read_video_frame(target_path, frame_number)
			if vision_frame is None:
				continue
			faces = get_many_faces([vision_frame])
			faces = sort_and_filter_faces(faces)
			for face in faces:
				if not is_duplicate_face(face, [f for f, _ in all_faces]):
					thumbnail = extract_face_thumbnail(vision_frame, face)
					all_faces.append((face, thumbnail))
	else:
		return {'success': False, 'message': '不支持的文件格式'}

	face_count = min(len(all_faces), 8)
	if face_count == 0:
		return {'success': False, 'message': '未检测到人脸'}

	# 保存缩略图（文件名加时间戳避免缓存和覆盖，同时清理旧缩略图）
	for old_file in os.listdir(THUMB_DIR):
		os.remove(os.path.join(THUMB_DIR, old_file))
	timestamp = int(time.time())
	face_results = []
	for idx, (face, thumbnail) in enumerate(all_faces[:8]):
		thumb_name = f'face_{idx}_{timestamp}.jpg'
		thumb_path = os.path.join(THUMB_DIR, thumb_name)
		cv2.imwrite(thumb_path, cv2.cvtColor(thumbnail, cv2.COLOR_RGB2BGR))
		face_results.append({
			'index': idx,
			'thumbnail_url': f'/uploads/thumbnails/{thumb_name}'
		})

	return {
		'success': True,
		'face_count': face_count,
		'faces': face_results
	}


@router.post('/upload/target')
async def upload_target(file : UploadFile = File(...)) -> dict:
	file_path = os.path.join(UPLOAD_DIR, file.filename)
	with open(file_path, 'wb') as f:
		content = await file.read()
		f.write(content)
	state_manager.set_item('target_path', file_path)
	return {
		'success': True,
		'path': file_path,
		'is_image': is_image(file_path),
		'is_video': is_video(file_path)
	}


@router.post('/upload/source')
async def upload_source(file : UploadFile = File(...)) -> dict:
	file_path = os.path.join(UPLOAD_DIR, file.filename)
	with open(file_path, 'wb') as f:
		content = await file.read()
		f.write(content)
	return {'success': True, 'path': file_path}


@router.post('/detect-faces')
async def api_detect_faces() -> dict:
	return detect_faces_from_target()


@router.post('/set-source-map')
async def set_source_map(data : dict) -> dict:
	state_manager.set_item('face_swapper_source_map', json.dumps(data.get('map', {})))
	return {'success': True}


PROCESSOR_OPTIONS = {
	'face_swapper': {
		'label': '换脸',
		'models': ['blendswap_256', 'ghost_1_256', 'ghost_2_256', 'ghost_3_256', 'hififace_unofficial_256', 'hyperswap_1a_256', 'hyperswap_1b_256', 'hyperswap_1c_256', 'inswapper_128', 'inswapper_128_fp16', 'simswap_256', 'simswap_unofficial_512', 'uniface_256'],
		'default_model': 'hyperswap_1a_256',
		'pixel_boost': {
			'blendswap_256': ['256x256', '384x384', '512x512', '768x768', '1024x1024'],
			'ghost_1_256': ['256x256', '512x512', '768x768', '1024x1024'],
			'ghost_2_256': ['256x256', '512x512', '768x768', '1024x1024'],
			'ghost_3_256': ['256x256', '512x512', '768x768', '1024x1024'],
			'hififace_unofficial_256': ['256x256', '512x512', '768x768', '1024x1024'],
			'hyperswap_1a_256': ['256x256', '512x512', '768x768', '1024x1024'],
			'hyperswap_1b_256': ['256x256', '512x512', '768x768', '1024x1024'],
			'hyperswap_1c_256': ['256x256', '512x512', '768x768', '1024x1024'],
			'inswapper_128': ['128x128', '256x256', '384x384', '512x512', '768x768', '1024x1024'],
			'inswapper_128_fp16': ['128x128', '256x256', '384x384', '512x512', '768x768', '1024x1024'],
			'simswap_256': ['256x256', '512x512', '768x768', '1024x1024'],
			'simswap_unofficial_512': ['512x512', '768x768', '1024x1024'],
			'uniface_256': ['256x256', '512x512', '768x768', '1024x1024']
		},
		'default_pixel_boost': '512x512',
		'weight': {'min': 0.0, 'max': 1.0, 'step': 0.05, 'default': 0.5}
	},
	'face_enhancer': {
		'label': '面部增强',
		'models': ['codeformer', 'gfpgan_1.2', 'gfpgan_1.3', 'gfpgan_1.4', 'gpen_bfr_256', 'gpen_bfr_512', 'gpen_bfr_1024', 'gpen_bfr_2048', 'restoreformer_plus_plus'],
		'default_model': 'gfpgan_1.4',
		'weight': {'min': 0.0, 'max': 1.0, 'step': 0.05, 'default': 0.5}
	},
	'frame_enhancer': {
		'label': '帧增强',
		'models': ['clear_reality_x4', 'face_dat_x4', 'lsdir_x4', 'nomos8k_sc_x4', 'real_esrgan_x2', 'real_esrgan_x2_fp16', 'real_esrgan_x4', 'real_esrgan_x4_fp16', 'real_esrgan_x8', 'real_esrgan_x8_fp16', 'real_hatgan_x4', 'real_web_photo_x4', 'realistic_rescaler_x4', 'remacri_x4', 'siax_x4', 'span_kendata_x4', 'swin2_sr_x4', 'tghq_face_x8', 'ultra_sharp_x4', 'ultra_sharp_2_x4'],
		'default_model': 'span_kendata_x4'
	}
}


@router.get('/processor-options')
async def get_processor_options() -> dict:
	return {'success': True, 'options': PROCESSOR_OPTIONS}


@router.post('/start-swap')
async def start_swap(data : dict) -> dict:
	from facefusion.core import conditional_process
	try:
		# 自动设置输出路径
		target_path = state_manager.get_item('target_path')
		if target_path:
			base, ext = os.path.splitext(target_path)
			output_path = base + '_swapped' + ext
			state_manager.set_item('output_path', output_path)

		# 设置处理器列表
		processors = data.get('processors', ['face_swapper'])
		state_manager.set_item('processors', processors)

		# 设置处理器参数
		processor_options = data.get('processor_options', {})
		for key, value in processor_options.items():
			state_manager.set_item(key, value)

		# 输出参数默认值
		if state_manager.get_item('output_video_scale') is None:
			state_manager.set_item('output_video_scale', 1.0)
		if state_manager.get_item('output_video_quality') is None:
			state_manager.set_item('output_video_quality', 80)
		if state_manager.get_item('output_video_preset') is None:
			state_manager.set_item('output_video_preset', 'veryfast')
		if state_manager.get_item('output_audio_volume') is None:
			state_manager.set_item('output_audio_volume', 100)
		if state_manager.get_item('output_video_fps') is None:
			from facefusion.media.vision import detect_video_fps
			video_path = state_manager.get_item('target_path')
			if video_path:
				state_manager.set_item('output_video_fps', detect_video_fps(video_path))

		# 默认参考帧
		if state_manager.get_item('reference_frame_number') is None:
			state_manager.set_item('reference_frame_number', 1)

		error_code = conditional_process()
		return {'success': error_code == 0, 'error_code': error_code, 'output_path': state_manager.get_item('output_path')}
	except Exception as exception:
		logger.error(str(exception), __name__)
		return {'success': False, 'message': str(exception)}


@router.websocket('/ws/progress')
async def progress_ws(websocket : WebSocket):
	await websocket.accept()
	try:
		while True:
			from facefusion import process_manager
			await websocket.send_json({'processing': process_manager.is_processing()})
			import asyncio
			await asyncio.sleep(1)
	except Exception:
		pass
