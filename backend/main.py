from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import logging
import traceback
import sys
import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import unquote
import os
import tempfile
from pathlib import Path
import io

# 配置详细的日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Length", "Content-Range", "Content-Type"]
)

class VideoURL(BaseModel):
    url: str

def get_filename_from_url(url: str) -> str:
    """从URL中提取文件名"""
    try:
        # 解码URL
        decoded_url = unquote(url)
        # 尝试从路径中获取文件名
        filename = os.path.basename(decoded_url.split('?')[0])
        # 如果没有扩展名，添加.mp4
        if not filename.endswith('.mp4'):
            filename += '.mp4'
        return filename
    except:
        # 如果出现任何错误，返回默认文件名
        return 'facebook_video.mp4'

async def download_video(url: str):
    """下载视频并返回字节数据"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Encoding': 'identity;q=1, *;q=0',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Range': 'bytes=0-',
            'Referer': 'https://www.facebook.com/',
            'Sec-Fetch-Dest': 'video',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'cross-site',
        }
        
        timeout = 30  # 设置30秒超时
        
        # 首先发送 HEAD 请求检查视频是否可访问
        head_response = requests.head(url, headers=headers, allow_redirects=True, timeout=timeout)
        if head_response.status_code == 403:
            raise HTTPException(status_code=403, detail="Access denied. The video URL might have expired or requires authentication.")
        elif head_response.status_code != 200:
            raise HTTPException(status_code=head_response.status_code, detail=f"Failed to access video: HTTP {head_response.status_code}")
        
        # 获取文件大小
        content_length = head_response.headers.get('content-length')
        if content_length:
            file_size = int(content_length)
            logger.info(f"Video size: {file_size / (1024*1024):.2f} MB")
            if file_size > 500 * 1024 * 1024:  # 如果文件大于500MB
                raise HTTPException(status_code=413, detail="Video file is too large to download")
        
        logger.info(f"Starting download from: {url}")
        
        # 下载视频
        with requests.get(url, headers=headers, stream=True, timeout=timeout) as response:
            response.raise_for_status()
            
            # 使用 BytesIO 作为内存缓冲区
            buffer = io.BytesIO()
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    buffer.write(chunk)
            
            # 获取所有数据
            video_data = buffer.getvalue()
            logger.info(f"Download completed, size: {len(video_data) / (1024*1024):.2f} MB")
            return video_data
            
    except requests.exceptions.Timeout:
        logger.error("Request timed out")
        raise HTTPException(status_code=504, detail="Request timed out while accessing the video")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading video: {str(e)}")
        if "Max retries exceeded" in str(e):
            raise HTTPException(status_code=504, detail="Failed to connect to video server")
        raise HTTPException(status_code=500, detail=f"Failed to download video: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during download: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/")
async def read_root():
    return {"status": "ok", "message": "Server is running"}

@app.get("/test")
async def test_endpoint():
    return {"status": "ok", "message": "Test endpoint is working"}

@app.post("/api/get-video")
async def get_video_url(video_url: VideoURL):
    try:
        url = video_url.url.strip()
        logger.info(f"Processing URL: {url}")

        # 设置请求头，模拟浏览器行为
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        }

        # 获取页面内容，设置较短的超时时间
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            html_content = response.text
        except requests.Timeout:
            logger.error("Request to Facebook timed out")
            raise HTTPException(
                status_code=504,
                detail="Request to Facebook timed out. Please try again."
            )
        except requests.RequestException as e:
            logger.error(f"Failed to fetch Facebook page: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch Facebook page: {str(e)}"
            )

        # 保存HTML内容用于调试
        with open("debug_page.html", "w", encoding="utf-8") as f:
            f.write(html_content)

        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        scripts = soup.find_all('script')
        
        # 保存所有脚本内容用于调试
        with open("debug_scripts.txt", "w", encoding="utf-8") as f:
            for script in scripts:
                f.write(str(script))
                f.write("\n---\n")

        # 尝试不同的方法来查找视频URL
        video_url = None
        
        # 查找包含视频URL的script标签
        patterns = [
            r'playable_url_quality_hd":"([^"]+)"',
            r'playable_url":"([^"]+)"',
            r'"video_url":"([^"]+)"',
            r'"video":{"url":"([^"]+)"',
            r'hd_src:"([^"]+)"',
            r'sd_src:"([^"]+)"',
            r'"browser_native_hd_url":"([^"]+)"',
            r'"browser_native_sd_url":"([^"]+)"',
            r'"dash_url":"([^"]+)"',
            r'"playback_url":"([^"]+)"'
        ]
        
        for script in scripts:
            script_text = str(script)
            for pattern in patterns:
                matches = re.findall(pattern, script_text)
                if matches:
                    video_url = matches[0].replace('\\/', '/')
                    logger.info(f"Found video URL using pattern: {pattern}")
                    break
            if video_url:
                break

        if video_url:
            logger.info(f"Found video URL: {video_url}")
            return {"success": True, "video_url": video_url}
        else:
            logger.error("No video URL found in the page")
            raise HTTPException(
                status_code=404,
                detail="Could not find video URL in the page. This might be due to Facebook's content protection."
            )

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

@app.get("/api/download")
async def download_video_endpoint(video_url: str, request: Request):
    """下载视频的端点"""
    try:
        logger.info(f"Download request from: {request.client.host}")
        logger.info(f"Request headers: {request.headers}")
        logger.info(f"Downloading video from: {video_url}")
        
        # 验证视频 URL
        if not video_url:
            raise HTTPException(status_code=400, detail="Video URL is required")
        
        if not video_url.startswith(('http://', 'https://')):
            raise HTTPException(status_code=400, detail="Invalid video URL")
        
        # 获取文件名
        filename = get_filename_from_url(video_url)
        logger.debug(f"Generated filename: {filename}")
        
        # 下载视频
        video_data = await download_video(video_url)
        
        # 创建响应头
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "video/mp4",
            "Content-Length": str(len(video_data)),
            "Accept-Ranges": "bytes",
            "Access-Control-Expose-Headers": "Content-Disposition, Content-Length",
            "Access-Control-Allow-Origin": "http://localhost:3000",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Cache-Control": "no-cache"
        }
        
        logger.info(f"Sending response with headers: {headers}")
        
        # 返回视频数据
        return Response(
            content=video_data,
            media_type="video/mp4",
            headers=headers
        )
        
    except HTTPException as he:
        logger.error(f"HTTP Exception in download endpoint: {str(he)}")
        raise he
    except Exception as e:
        logger.error(f"Error in download endpoint: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8001,
        reload=True,
        log_level="debug",
        workers=1
    )
