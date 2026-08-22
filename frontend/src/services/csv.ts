import { apiClient } from './api';
import type { CsvAnalysisResponse } from '../types';

export const csvService = {
  async analyzeCsv(file: File): Promise<CsvAnalysisResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const res = await apiClient.post<CsvAnalysisResponse>('/csv/analyze', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res;
  },
};
