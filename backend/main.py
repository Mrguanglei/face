import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from facefusion import metadata, state_manager
from facefusion.utils.filesystem import resolve_relative_path

from backend.api import router


def create_app() -> FastAPI:
	app = FastAPI(title = metadata.get('name') + ' ' + metadata.get('version'))

	# CORS
	app.add_middleware(
		CORSMiddleware,
		allow_origins = [ '*' ],
		allow_credentials = True,
		allow_methods = [ '*' ],
		allow_headers = [ '*' ]
	)

	# 静态文件（上传目录）
	uploads_dir = resolve_relative_path('uploads')
	os.makedirs(uploads_dir, exist_ok = True)
	app.mount('/uploads', StaticFiles(directory = uploads_dir), name = 'uploads')

	# 自定义 API
	app.include_router(router)

	return app


def run_server() -> None:
	app = create_app()
	uvicorn.run(app, host = '0.0.0.0', port = 7860, log_level = 'info')


if __name__ == '__main__':
	run_server()
