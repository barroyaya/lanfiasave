// src/pages/Login.js
import React, { useState } from 'react';
import axios from 'axios';
import { Container, Form, Button, Alert } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/users/login_api/",
        { username, password },
        {
          headers: { 'Content-Type': 'application/json' },
          withCredentials: true, // pour envoyer les cookies de session
        }
      );
      if (response.data.success) {
        navigate('/profile'); // Redirection vers la page de profil
      } else {
        setError(response.data.message || "Une erreur est survenue.");
      }
    } catch (err) {
      console.error("Erreur lors de la connexion :", err);
      setError("Nom d'utilisateur ou mot de passe incorrect.");
    }
  };

  return (
    <Container className="mt-5">
      <h2>Connexion</h2>
      {error && <Alert variant="danger">{error}</Alert>}
      <Form onSubmit={handleLogin}>
        <Form.Group className="mb-3">
          <Form.Label>Nom d'utilisateur</Form.Label>
          <Form.Control
            type="text"
            value={username}
            onChange={e => setUsername(e.target.value)}
            required
          />
        </Form.Group>
        <Form.Group className="mb-3">
          <Form.Label>Mot de passe</Form.Label>
          <Form.Control
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
          />
        </Form.Group>
        <Button variant="primary" type="submit">
          Se connecter
        </Button>
      </Form>
    </Container>
  );
};

export default Login;
