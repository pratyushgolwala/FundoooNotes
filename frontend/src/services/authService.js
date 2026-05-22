import API from './api';

const authService = {
  signup: (data) =>
    API.post('/signup/', {
      username: data.username,
      email: data.email,
      phone_number: data.phone_number,
      password: data.password,
    }),

  login: (data) =>
    API.post('/login/', {
      username: data.username,
      password: data.password,
    }),

  verifyOtp: (data) =>
    API.post('/verify-otp/', {
      user_id: data.user_id,
      otp: data.otp,
    }),

  refreshToken: (refreshToken) =>
    API.post('/refresh-token/', {
      refresh_token: refreshToken,
    }),
};

export default authService;
