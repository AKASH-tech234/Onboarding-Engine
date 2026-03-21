import axios from 'axios';
import { getApiBaseUrl } from '../config/api';

const client = axios.create({
  baseURL: getApiBaseUrl(),
});

export default client;
