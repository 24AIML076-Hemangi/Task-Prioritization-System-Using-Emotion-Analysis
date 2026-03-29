const LOCAL_API_URL = "http://localhost:5000";
const PROD_API_URL = "https://task-prioritization-system-using-emotion.onrender.com";

const isLocalhost = ["localhost", "127.0.0.1"].includes(window.location.hostname);

export const BASE_URL = isLocalhost ? LOCAL_API_URL : PROD_API_URL;
