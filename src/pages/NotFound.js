import React from 'react';
import { Container } from 'react-bootstrap';

const NotFound = () => {
    return (
        <Container className="mt-5 text-center">
            <h1 className="text-danger">404 - Page non trouvée</h1>
            <p>La page que vous cherchez n'existe pas.</p>
        </Container>
    );
};

export default NotFound;
