import React, { useEffect, useState } from "react";
import axios from "axios";
import {
  Container,
  Card,
  Spinner,
  Alert,
  Table,
  Button,
  Row,
  Col
} from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import Cookies from "js-cookie";

const Profile = () => {
  const [profileData, setProfileData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await axios.get(
          "http://127.0.0.1:8000/users/profile_api/",
          {
            withCredentials: true,
            headers: {
              "X-CSRFToken": Cookies.get("csrftoken"),
              "Content-Type": "application/json",
            },
          }
        );
console.log('CSRF Token:', Cookies.get('csrftoken')); // Doit afficher une valeur
        if (response.data?.user) {
          setProfileData({
            ...response.data,
            personne: response.data.personne || null,
          });
        } else {
          throw new Error("Réponse serveur invalide");
        }
      } catch (err) {
        setError(err.message || "Erreur lors du chargement du profil");
        console.error("Erreur profil:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, []);

  const handleNavigation = (path) => {
    navigate(path);
  };

  if (loading) {
    return (
      <div className="d-flex justify-content-center mt-5">
        <Spinner animation="border" variant="primary" />
      </div>
    );
  }

  if (error) {
    return (
      <Container className="mt-5">
        <Alert variant="danger">{error}</Alert>
      </Container>
    );
  }

  if (!profileData?.user) {
    return (
      <Container className="mt-5">
        <Alert variant="warning">Profil utilisateur non trouvé</Alert>
      </Container>
    );
  }

  const { user, personne } = profileData;
  const isVulnerable = user.role === "Personne vulnérable";
  const isRecenseur = user.role === "Recenseur";

  return (
    <Container className="my-5">
      <Card className="shadow-lg">
        <Card.Header className="bg-primary text-white">
          <h2 className="mb-0">Profil de {user.username}</h2>
        </Card.Header>

        <Card.Body>
          {/* Section Rôle */}
          <Row className="mb-4">
            <Col>
              <h4 className="text-muted">Rôle</h4>
              <p className="h5">{user.role}</p>
              {isRecenseur && (
                <div className="mt-3">
                  <p className="lead">
                    Recensements effectués: {user.recensements.count}
                  </p>
                </div>
              )}
            </Col>
          </Row>

          {/* Section Personne Vulnérable */}
          {isVulnerable && (
            <Row className="mb-4">
              <Col>
                <h4 className="border-bottom pb-2 mb-3">
                  Informations de bénéficiaire
                </h4>

                {personne ? (
                  <>
                    <div className="mb-3">
                      <strong>Total reçu:</strong>{" "}
                      {personne.montant_total?.toFixed(2)} €
                    </div>

                    <h5>Historique des dons</h5>
                    {personne.dons_recus?.length > 0 ? (
                      <Table striped hover responsive className="mt-3">
                        <thead>
                          <tr>
                            <th>Date</th>
                            <th>Montant</th>
                            <th>Description</th>
                          </tr>
                        </thead>
                        <tbody>
                          {personne.dons_recus.map((don, index) => (
                            <tr key={index}>
                              <td>{don.date_don || "Non spécifiée"}</td>
                              <td>{don.montant_recu?.toFixed(2)} €</td>
                              <td>{don.description || "-"}</td>
                            </tr>
                          ))}
                        </tbody>
                      </Table>
                    ) : (
                      <Alert variant="info" className="mt-3">
                        Aucun don reçu pour le moment
                      </Alert>
                    )}
                  </>
                ) : (
                  <Alert variant="warning">
                    Profil bénéficiaire non configuré
                  </Alert>
                )}
              </Col>
            </Row>
          )}

          {/* Actions */}
          <Row className="mt-4">
            <Col className="d-flex gap-3">
              <Button
                variant="outline-danger"
                onClick={() => handleNavigation("/logout")}
              >
                Déconnexion
              </Button>

              <Button
                variant="outline-secondary"
                onClick={() => handleNavigation("/change-password")}
              >
                Changer le mot de passe
              </Button>
            </Col>
          </Row>
        </Card.Body>
      </Card>
    </Container>
  );
};

export default Profile;