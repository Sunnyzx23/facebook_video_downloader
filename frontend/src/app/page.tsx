'use client';

import { useState } from 'react';
import axios from 'axios';

// API 基础URL
const API_BASE_URL = 'http://127.0.0.1:8001';

export default function Home() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [videoUrl, setVideoUrl] = useState('');
  const [showSuccess, setShowSuccess] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Submitting URL:', url);
    
    if (!url) {
      setError('Please enter a Facebook video URL');
      return;
    }

    setLoading(true);
    setError('');
    setVideoUrl('');
    setShowSuccess(false);

    try {
      console.log('Making API request...');
      const response = await axios.post(`${API_BASE_URL}/api/get-video`, 
        { url: url.trim() },
        { 
          timeout: 60000,  // 60 seconds timeout
          headers: {
            'Content-Type': 'application/json',
          }
        }
      );
      
      console.log('API Response:', response.data);

      if (response.data.success) {
        setVideoUrl(response.data.video_url);
        setShowSuccess(true);
      } else {
        setError('Failed to get video URL');
      }
    } catch (err: any) {
      console.error('Error details:', err);
      
      if (err.code === 'ECONNABORTED') {
        setError('Request timed out. Please try again.');
      } else if (err.response) {
        // Server responded with error
        const errorMessage = err.response.data?.detail || err.response.data?.message || 'An error occurred';
        setError(`Error: ${errorMessage}`);
      } else if (err.request) {
        // Request was made but no response
        setError('Could not connect to the server. Please check if the server is running.');
      } else {
        // Something else went wrong
        setError(err.message || 'An unexpected error occurred');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!videoUrl) {
      console.log('No video URL provided');
      return;
    }

    setDownloading(true);
    setDownloadProgress(0);
    
    try {
      console.log('Starting download...');
      
      // 首先获取视频信息
      const response = await fetch(`${API_BASE_URL}/api/download?video_url=${encodeURIComponent(videoUrl)}`, {
        method: 'GET',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // 获取文件名
      const contentDisposition = response.headers.get('content-disposition');
      let filename = 'video.mp4';
      if (contentDisposition) {
        const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(contentDisposition);
        if (matches != null && matches[1]) {
          filename = matches[1].replace(/['"]/g, '');
        }
      }

      console.log('Received response, creating blob...');
      const blob = await response.blob();
      console.log('Blob created, size:', blob.size);

      // 创建下载链接
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      
      // 触发下载
      document.body.appendChild(link);
      link.click();
      
      // 清理
      window.URL.revokeObjectURL(url);
      link.remove();
      
      console.log('Download completed successfully');
      setDownloading(false);
      setDownloadProgress(100);
      
    } catch (error) {
      console.error('Download failed:', error);
      setDownloading(false);
      setDownloadProgress(0);
      // 显示错误消息
      alert('Download failed. Please try again.');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100 p-4">
      <div className="max-w-md mx-auto bg-white rounded-xl shadow-lg p-6 mt-10">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            Facebook Video Downloader
          </h1>
          <p className="text-gray-600">
            Download your favorite Facebook videos easily
          </p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative">
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Paste Facebook video URL here"
              className="w-full p-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            {url && (
              <button
                type="button"
                onClick={() => setUrl('')}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            )}
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className={`w-full p-4 rounded-lg font-semibold text-white transition-all duration-200
              ${loading 
                ? 'bg-blue-400 cursor-not-allowed' 
                : 'bg-blue-500 hover:bg-blue-600 active:transform active:scale-[0.99]'}`}
          >
            {loading ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Processing...
              </span>
            ) : 'Get Download Link'}
          </button>
        </form>

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg">
            <div className="flex items-center">
              <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
              </svg>
              {error}
            </div>
          </div>
        )}

        {showSuccess && videoUrl && (
          <div className="mt-6 space-y-4">
            <div className="p-4 bg-green-50 border border-green-200 text-green-700 rounded-lg">
              <div className="flex items-center">
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
                </svg>
                Video link generated successfully!
              </div>
            </div>
            
            <button
              onClick={handleDownload}
              disabled={downloading}
              className={`w-full p-4 rounded-lg font-semibold text-white transition-all duration-200 flex items-center justify-center space-x-2
                ${downloading 
                  ? 'bg-green-400 cursor-not-allowed' 
                  : 'bg-green-500 hover:bg-green-600 active:bg-green-700'}`}
            >
              {downloading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Downloading...
                </span>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                  </svg>
                  <span>Download Video</span>
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
