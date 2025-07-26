import React from 'react';
import { Container, Row, Col, Card, Button, Carousel } from 'react-bootstrap';

const Home = () => {
  return (
    <Container className="mt-5">
      {/* Message général avant les témoignages */}
      <Row className="mb-5">
        <Col>
          <Card className="bg-light text-center p-4">
            <Card.Body>
              <Card.Title className="display-5 text-primary">Notre Mission</Card.Title>
              <Card.Text className="lead">
                Nous nous engageons à soutenir les personnes vulnérables en Côte d'Ivoire en leur offrant une aide
                concrète. Chaque don compte et permet de transformer des vies. Découvrez comment votre générosité fait
                la différence !
              </Card.Text>
              <Button variant="success" size="lg">Faire un Don Maintenant</Button>
            </Card.Body>
          </Card>
        </Col>
      </Row>



      {/* Carousel de témoignages */}
      <Row className="mb-5">
        <Col>
          <Carousel>
            <Carousel.Item>
              <img
                className="d-block w-100"
                src="/don.jpeg"
                alt="Impact du don"
                style={{ maxHeight: '400px', objectFit: 'cover' }}
              />
              <Carousel.Caption className="text-center">
                <h3>Un don peut changer une vie</h3>
                <p>
                  Grâce à votre soutien, Aïcha a pu reprendre sa formation professionnelle et envisager un avenir
                  meilleur.
                </p>
              </Carousel.Caption>
            </Carousel.Item>
            <Carousel.Item>
              <img
                className="d-block w-100"
                src="/p4.jpg"
                alt="Soutien aux bénéficiaires"
                style={{ maxHeight: '400px', objectFit: 'cover' }}
              />
              <Carousel.Caption className="text-center">
                <h3>Soutien Concret</h3>
                <p>
                  Mamadou témoigne : "Votre don m'a permis de subvenir aux besoins essentiels de ma famille."
                </p>
              </Carousel.Caption>
            </Carousel.Item>
            <Carousel.Item>
              <img
                className="d-block w-100"
                src="/p2.jpg"
                alt="Changez des vies"
                style={{ maxHeight: '400px', objectFit: 'cover' }}
              />
              <Carousel.Caption className="text-center">
                <h3>Changez des vies</h3>
                <p>
                  Fatou raconte : "Grâce à votre générosité, j'ai pu accéder à des soins essentiels. Merci !"
                </p>
              </Carousel.Caption>
            </Carousel.Item>
          </Carousel>
        </Col>
      </Row>

      {/* En-tête */}
      <Row className="mb-4 text-center">
        <Col>
          <h1 className="display-4 text-primary">Soutenez Nos Bénéficiaires</h1>
          <p className="lead">
            Votre don peut changer une vie. Découvrez les témoignages inspirants et l'impact de votre générosité sur
            la vie des personnes vulnérables en Côte d'Ivoire.
          </p>
          <Button variant="success" size="lg">Faites un don dès maintenant</Button>
        </Col>
      </Row>

      {/* Présentation des bénéficiaires */}
      <Row className="mb-5">
        <Col md={4}>
          <Card className="h-100 text-center">
            <Card.Img
              variant="top"
              src="/im3.jpeg"
              style={{ maxHeight: '200px', objectFit: 'cover' }}
            />
            <Card.Body>
              <Card.Title>Aïcha, 28 ans</Card.Title>
              <Card.Text>
                "Grâce à l'aide reçue, j'ai pu reprendre ma formation professionnelle et envisager un avenir meilleur."
              </Card.Text>
            </Card.Body>
            <Card.Footer>
              <small className="text-muted">Impact réel</small>
            </Card.Footer>
          </Card>
        </Col>
        <Col md={4}>
          <Card className="h-100 text-center">
            <Card.Img
              variant="top"
              src="/im1.jpeg"
              style={{ maxHeight: '200px', objectFit: 'cover' }}
            />
            <Card.Body>
              <Card.Title>Mamadou, 45 ans</Card.Title>
              <Card.Text>
                "Votre don a transformé ma vie. Aujourd'hui, je peux subvenir aux besoins de ma famille grâce à votre aide."
              </Card.Text>
            </Card.Body>
            <Card.Footer>
              <small className="text-muted">Témoignage inspirant</small>
            </Card.Footer>
          </Card>
        </Col>
        <Col md={4}>
          <Card className="h-100 text-center">
            <Card.Img
              variant="top"
              src="/im2.jpeg"
              style={{ maxHeight: '200px', objectFit: 'cover' }}
            />
            <Card.Body>
              <Card.Title>Fatou, 32 ans</Card.Title>
              <Card.Text>
                "Votre générosité m'a permis d'accéder à des soins essentiels. Merci de croire en moi et de m'aider à avancer."
              </Card.Text>
            </Card.Body>
            <Card.Footer>
              <small className="text-muted">Soutien vital</small>
            </Card.Footer>
          </Card>
        </Col>
      </Row>

      {/* Appel à l'action */}
      <Row className="text-center mb-5">
        <Col>
          <Button variant="success" size="lg">Faire un Don Maintenant</Button>
        </Col>
      </Row>
    </Container>
  );
};

export default Home;
