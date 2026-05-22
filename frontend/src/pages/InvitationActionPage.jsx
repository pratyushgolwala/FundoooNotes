import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import notesService from '../services/notesService';
import '../styles/auth.css';
import { FaCheckCircle, FaTimesCircle, FaHourglassHalf, FaArrowRight } from 'react-icons/fa';

export default function InvitationActionPage() {
  const { token, action } = useParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('loading');
  const [message, setMessage] = useState('Processing invitation...');

  useEffect(() => {
    const runInvitationAction = async () => {
      if (!token || !action) {
        setStatus('error');
        setMessage('Invalid invitation link.');
        return;
      }

      try {
        const response = action === 'accept'
          ? await notesService.acceptNoteInvitation(token)
          : await notesService.declineNoteInvitation(token);

        setStatus(action === 'accept' ? 'success' : 'declined');
        setMessage(response?.data?.detail || (action === 'accept' ? 'Invitation accepted.' : 'Invitation declined.'));
      } catch (err) {
        setStatus('error');
        setMessage(err.response?.data?.detail || 'Could not process invitation.');
      }
    };

    runInvitationAction();
  }, [token, action]);

  const statusIcon = () => {
    if (status === 'loading') return <FaHourglassHalf />;
    if (status === 'success') return <FaCheckCircle />;
    if (status === 'declined') return <FaTimesCircle />;
    return <FaTimesCircle />;
  };

  return (
    <div className="auth-page">
      <div className="auth-card invitation-card">
        <div className="auth-header">
          <h1>Invitation</h1>
          <p className="auth-subtitle">{statusIcon()} {message}</p>
        </div>

        <div className="auth-toggle" style={{ marginTop: 0 }}>
          <button className="auth-btn" onClick={() => navigate('/dashboard')}>
            Go to Dashboard <FaArrowRight />
          </button>
        </div>
      </div>
    </div>
  );
}