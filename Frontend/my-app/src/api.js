import axios from 'axios';

const API_URL = 'http://127.0.0.1:8000'; // adjust if hosted elsewhere

// ✅ Register new user
const registerUser = async (userData) => {
  try {
    await axios.post(`${API_URL}/auth/register`, userData);
  } catch (error) {
    console.error("Registration error:", error);
    throw error;
  }
};

// ✅ Login user with email/password and receive JWT token
const loginUser = async (credentials) => {
  try {
    const params = new URLSearchParams();
    for (const key in credentials) {
      params.append(key, credentials[key]);
    }

    const response = await axios.post(`${API_URL}/auth/login`, params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    return response.data; // returns { access_token, token_type }
  } catch (error) {
    console.error("Login error:", error);
    throw error;
  }
};

// ✅ Fetch user profile using token (calls /auth/me)
const fetchUserProfile = async (token) => {
  try {
    const response = await axios.get(`${API_URL}/auth/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    return response.data; // returns user { id, username, email, role }
  } catch (error) {
    console.error("Fetch user profile error:", error);
    throw error;
  }
};

export { registerUser, loginUser, fetchUserProfile };
