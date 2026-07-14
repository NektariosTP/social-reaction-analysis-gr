import { client } from "../client/client.gen";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://localhost:8000";

client.setConfig({ baseUrl: API_BASE_URL });

export { API_BASE_URL };
