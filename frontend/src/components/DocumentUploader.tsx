import React, { useState } from 'react';
import { ingestFile } from '../api/aiApi';
import toast from 'react-hot-toast';

interface DocumentUploaderProps {
  sessionId: string;
}

const DocumentUploader: React.FC<DocumentUploaderProps> = ({ sessionId }) => {
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleFileUpload = async (file: File) => {
    setIsUploading(true);
    setUploadProgress(0);
    setSuccessMessage(null);

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Authentication token is missing. Please log in again.');
      }

      const xhr = new XMLHttpRequest();
      xhr.open('POST', `${process.env.REACT_APP_API_BASE_URL}/api/documents/upload`, true);
      xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      xhr.setRequestHeader('session-id', sessionId);

      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const progress = Math.round((event.loaded / event.total) * 100);
          setUploadProgress(progress);
        }
      };

      xhr.onload = () => {
        setIsUploading(false);
        if (xhr.status >= 200 && xhr.status < 300) {
          const contentType = xhr.getResponseHeader('Content-Type');
          if (contentType && contentType.includes('application/json')) {
            const response = JSON.parse(xhr.responseText);
            setSuccessMessage(`✓ Indexed ${response.chunks_indexed} chunks`);
          } else {
            throw new Error('Unexpected response format from server.');
          }
        } else {
          const contentType = xhr.getResponseHeader('Content-Type');
          if (contentType && contentType.includes('application/json')) {
            const errorResponse = JSON.parse(xhr.responseText);
            throw new Error(errorResponse.message || 'An error occurred during file upload.');
          } else {
            throw new Error('An error occurred during file upload.');
          }
        }
      };

      xhr.onerror = () => {
        setIsUploading(false);
        throw new Error('Network error occurred during file upload.');
      };

      const formData = new FormData();
      formData.append('file', file);
      xhr.send(formData);
    } catch (error: any) {
      setIsUploading(false);
      toast.error(error.message || 'An unexpected error occurred.');
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const files = event.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      if (['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'].includes(file.type)) {
        handleFileUpload(file);
      } else {
        toast.error('Unsupported file type. Please upload a .pdf, .docx, .xlsx, or .xls file.');
      }
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'].includes(file.type)) {
        handleFileUpload(file);
      } else {
        toast.error('Unsupported file type. Please upload a .pdf, .docx, .xlsx, or .xls file.');
      }
    }
  };

  return (
    <div className="w-full max-w-lg mx-auto p-4 border-2 border-dashed border-gray-300 rounded-lg bg-gray-50">
      <div
        className="flex flex-col items-center justify-center h-40 cursor-pointer"
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
      >
        <p className="text-gray-500">Drag and drop your file here</p>
        <p className="text-gray-400 text-sm">or</p>
        <label
          htmlFor="file-upload"
          className="cursor-pointer text-blue-500 underline"
        >
          Browse files
        </label>
        <input
          id="file-upload"
          type="file"
          className="hidden"
          onChange={handleFileSelect}
          accept=".pdf,.docx,.xlsx,.xls"
        />
      </div>
      {isUploading && (
        <div className="mt-4">
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div
              className="bg-blue-500 h-2.5 rounded-full"
              style={{ width: `${uploadProgress}%` }}
            ></div>
          </div>
          <p className="text-sm text-gray-500 mt-2">
            Uploading... {uploadProgress}%
          </p>
        </div>
      )}
      {successMessage && (
        <div className="mt-4 text-green-600 font-semibold">{successMessage}</div>
      )}
    </div>
  );
};

export default DocumentUploader;