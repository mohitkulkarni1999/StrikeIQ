import api from '@/lib/api';

export interface ExpiryResponse {
  symbol: string;
  expiries: string[];
}

export const fetchAvailableExpiries = async (symbol: string): Promise<string[]> => {
  try {
    const response = await api.get<ExpiryResponse>(`/api/v1/market/expiries?symbol=${symbol}`);
    return response.data.expiries || [];
  } catch (error) {
    console.error('Failed to fetch expiries:', error);
    return [];
  }
};
