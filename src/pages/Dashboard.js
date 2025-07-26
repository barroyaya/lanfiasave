// src/pages/Dashboard.jsx
import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import { Container, Row, Col, Card, Spinner } from 'react-bootstrap';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import PauvreteChart from '../components/PauvreteChart'; // Composant pour le graphique de pauvreté
import ChartComponent from '../components/ChartComponent'; // Composant générique pour les autres graphiques

const Dashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const mapRef = useRef(null);

  // Récupération des données depuis l'API Django
  useEffect(() => {
    axios.get("http://127.0.0.1:8000/donations/dashboard_api/")
      .then(response => {
        setData(response.data);
        setLoading(false);
        console.log("Dashboard data:", response.data);
      })
      .catch(error => {
        console.error("Erreur lors de la récupération des données :", error);
        setLoading(false);
      });
  }, []);

  // Initialisation de la carte Leaflet dès que les données sont chargées
  useEffect(() => {
    if (data?.regions_data && !mapRef.current) {
      mapRef.current = L.map('map');
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap'
      }).addTo(mapRef.current);

      data.regions_data.forEach(region => {
        if (region?.total_vulnerables > 0) {
          const radius = Math.min(5 + (region.total_vulnerables / 1), 40);
          L.circleMarker([region.lat, region.lng], {
            radius,
            color: '#e74c3c',
            fillColor: '#ff6b6b',
            fillOpacity: 0.7
          })
            .bindPopup(`
              <strong>${region?.name}</strong><br>
              Vulnérables: ${region?.total_vulnerables}<br>
              Non vulnérables: ${region?.total_non_vulnerables}
            `)
            .addTo(mapRef.current);
        }
      });
      const ivoireBounds = L.latLngBounds([[4.3, -8.0], [10.0, -2.0]]);
      mapRef.current.fitBounds(ivoireBounds);
    }
  }, [data]);

  if (loading) {
    return (
      <Container className="mt-5">
        <Spinner animation="border" variant="primary" />
      </Container>
    );
  }

  // Extraction sécurisée des données avec opérateur de chaînage et valeurs par défaut
  const statsPauvreteVulnerables = data?.stats_pauvrete_vulnerables ?? 0;
  const statsPauvreteNonVuln = data?.stats_pauvrete_non_vulnerables ?? 0;

  const regionLabels = data?.stats_region?.map(stat => stat.region_geographique || "Inconnu") ?? [];
  const regionVuln = data?.stats_region?.map(stat => stat.total_vulnerables) ?? [];
  const regionNonVuln = data?.stats_region?.map(stat => stat.total_non_vulnerables) ?? [];

  const entiteLabels = data?.stats_entite?.map(stat => stat.entite || "Autre") ?? [];
  const entiteVuln = data?.stats_entite?.map(stat => stat.total_vulnerables) ?? [];
  const entiteNonVuln = data?.stats_entite?.map(stat => stat.total_non_vulnerables) ?? [];

  const sexeLabels = data?.stats_sexe?.map(stat => stat.sexe) ?? [];
  const sexeVuln = data?.stats_sexe?.map(stat => stat.total_vulnerables) ?? [];
  const sexeNonVuln = data?.stats_sexe?.map(stat => stat.total_non_vulnerables) ?? [];

  const ageLabels = data?.stats_age?.map(stat => stat.age) ?? [];
  const ageVuln = data?.stats_age?.map(stat => stat.total_vulnerables) ?? [];
  const ageNonVuln = data?.stats_age?.map(stat => stat.total_non_vulnerables) ?? [];

  // Option commune pour tous les graphiques
  const commonChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 0 }
  };

  // Données pour le graphique "Niveaux de Pauvreté" (via PauvreteChart)
  const pauvreteData = {
    labels: ["Niveau de Pauvreté"],
    datasets: [
      {
        label: 'Personnes Vulnérables',
        data: [statsPauvreteVulnerables],
        backgroundColor: '#ff6b6b',
        borderColor: '#ff6b6b',
        borderWidth: 2,
        borderRadius: 5,
      },
      {
        label: 'Personnes Non Vulnérables',
        data: [statsPauvreteNonVuln],
        backgroundColor: '#4ecdc4',
        borderColor: '#4ecdc4',
        borderWidth: 2,
        borderRadius: 5,
      }
    ]
  };

  const pauvreteOptions = {
    ...commonChartOptions,
    scales: {
      y: { beginAtZero: true, title: { display: true, text: 'Nombre de Personnes' } },
      x: { title: { display: true, text: 'Catégorie' } }
    }
  };

  // Données pour le graphique "Pauvreté par Région"
  const regionChartData = {
    labels: regionLabels,
    datasets: [
      { label: 'Vulnérables', data: regionVuln, backgroundColor: '#ff6b6b', borderWidth: 1 },
      { label: 'Non Vulnérables', data: regionNonVuln, backgroundColor: '#4ecdc4', borderWidth: 1 }
    ]
  };
  const regionChartOptions = {
    ...commonChartOptions,
    scales: { y: { beginAtZero: true } }
  };

  // Données pour le graphique "Pauvreté par Entité"
  const entiteChartData = {
    labels: entiteLabels,
    datasets: [
      { label: 'Vulnérables', data: entiteVuln, backgroundColor: '#ff6b6b', borderWidth: 1 },
      { label: 'Non Vulnérables', data: entiteNonVuln, backgroundColor: '#4ecdc4', borderWidth: 1 }
    ]
  };
  const entiteChartOptions = {
    ...commonChartOptions,
    scales: { y: { beginAtZero: true } }
  };

  // Données pour le graphique "Pauvreté par Sexe"
  const sexeChartData = {
    labels: sexeLabels,
    datasets: [
      { label: 'Vulnérables', data: sexeVuln, backgroundColor: '#ff6b6b', borderWidth: 1 },
      { label: 'Non Vulnérables', data: sexeNonVuln, backgroundColor: '#4ecdc4', borderWidth: 1 }
    ]
  };
  const sexeChartOptions = {
    ...commonChartOptions,
    scales: { y: { beginAtZero: true } }
  };

  // Données pour le graphique "Évolution par Âge"
  const ageChartData = {
    labels: ageLabels,
    datasets: [
      {
        label: 'Vulnérables',
        data: ageVuln,
        borderColor: '#ff6b6b',
        backgroundColor: 'rgba(255, 107, 107, 0.2)',
        borderWidth: 2,
        fill: true,
        tension: 0.4
      },
      {
        label: 'Non Vulnérables',
        data: ageNonVuln,
        borderColor: '#4ecdc4',
        backgroundColor: 'rgba(78, 205, 196, 0.2)',
        borderWidth: 2,
        fill: true,
        tension: 0.4
      }
    ]
  };
  const ageChartOptions = {
    ...commonChartOptions,
    scales: { y: { beginAtZero: true } },
    elements: { point: { radius: 4, hoverRadius: 6 } }
  };

  return (
    <Container className="mt-4">
      {/* Cartes statistiques globales */}
      <Row className="mb-4">
        <Col md={4}>
          <Card className="text-center">
            <Card.Body>
              <Card.Title>Nombre total de personnes recensées</Card.Title>
              <Card.Text>{data?.nombre_personnes_total ?? 0}</Card.Text>
            </Card.Body>
          </Card>
        </Col>
        <Col md={4}>
          <Card className="text-center">
            <Card.Body>
              <Card.Title>Nombre de personnes ayant reçu un don</Card.Title>
              <Card.Text>{data?.nombre_personnes_aidees ?? 0}</Card.Text>
            </Card.Body>
          </Card>
        </Col>
        <Col md={4}>
          <Card className="text-center">
            <Card.Body>
              <Card.Title>Nombre total de personnes vulnérables</Card.Title>
              <Card.Text>{data?.nombre_personnes_vulnerables ?? 0}</Card.Text>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Indicateur de performance : Taux de Vulnérabilité Globale */}
      <Row className="mb-4">
        <Col md={12}>
          <Card className="text-center">
            <Card.Body>
              <Card.Title>Taux de Vulnérabilité Globale</Card.Title>
              <Card.Text>{data?.taux_vulnerabilite ?? 0}%</Card.Text>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Carte interactive */}
      <Row className="mb-4">
        <Col md={12}>
          <Card>
            <Card.Header>Carte des Vulnérabilités par Région</Card.Header>
            <Card.Body>
              <div id="map" style={{ height: "500px", borderRadius: "8px" }}></div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Grille des graphiques avec hauteur augmentée */}
      <Row className="mb-4">
        <Col md={4}>
          <Card>
            <Card.Header>Niveaux de Pauvreté</Card.Header>
            <Card.Body style={{ height: "400px" }}>
              <PauvreteChart data={pauvreteData} options={pauvreteOptions} />
            </Card.Body>
          </Card>
        </Col>
        <Col md={4}>
          <Card>
            <Card.Header>Pauvreté par Région</Card.Header>
            <Card.Body style={{ height: "400px" }}>
              <ChartComponent
                id="regionChart"
                type="bar"
                data={regionChartData}
                options={regionChartOptions}
              />
            </Card.Body>
          </Card>
        </Col>
        <Col md={4}>
          <Card>
            <Card.Header>Pauvreté par Catégorie</Card.Header>
            <Card.Body style={{ height: "400px" }}>
              <ChartComponent
                id="entiteChart"
                type="bar"
                data={entiteChartData}
                options={entiteChartOptions}
              />
            </Card.Body>
          </Card>
        </Col>
      </Row>
      <Row className="mb-4">
        <Col md={4}>
          <Card>
            <Card.Header>Pauvreté par Sexe</Card.Header>
            <Card.Body style={{ height: "400px" }}>
              <ChartComponent
                id="sexeChart"
                type="bar"
                data={sexeChartData}
                options={sexeChartOptions}
              />
            </Card.Body>
          </Card>
        </Col>
        <Col md={4}>
          <Card>
            <Card.Header>Évolution par Âge</Card.Header>
            <Card.Body style={{ height: "400px" }}>
              <ChartComponent
                id="ageChart"
                type="line"
                data={ageChartData}
                options={ageChartOptions}
              />
            </Card.Body>
          </Card>
        </Col>
        <Col md={4}>
          <Card>
            <Card.Header>Enfants Pris en Charge</Card.Header>
            <Card.Body style={{ height: "400px" }}>
              <ChartComponent
                id="enfantsChart"
                type="bar"
                data={{
                  labels: ['Enfants Pris en Charge'],
                  datasets: [
                    {
                      label: 'Vulnérables',
                      data: [data?.stats_enfants?.enfants_vulnerables ?? 0],
                      backgroundColor: '#ff6b6b',
                      borderWidth: 2,
                      borderRadius: 5,
                    },
                    {
                      label: 'Non Vulnérables',
                      data: [data?.stats_enfants?.enfants_non_vulnerables ?? 0],
                      backgroundColor: '#4ecdc4',
                      borderWidth: 2,
                      borderRadius: 5,
                    }
                  ]
                }}
                options={{
                  ...commonChartOptions,
                  scales: {
                    y: { beginAtZero: true, title: { display: true, text: 'Nombre d’Enfants' } },
                    x: { title: { display: true, text: 'Catégorie' } }
                  }
                }}
              />
            </Card.Body>
          </Card>
        </Col>
      </Row>
      <Row className="mb-4">
        <Col md={12}>
          <Card>
            <Card.Header>Répartition Globale</Card.Header>
            <Card.Body style={{ height: "400px" }}>
              <ChartComponent
                id="globalDistributionChart"
                type="pie"
                data={{
                  labels: ['Vulnérables', 'Non Vulnérables'],
                  datasets: [{
                    data: [statsPauvreteVulnerables, statsPauvreteNonVuln],
                    backgroundColor: ['#ff6b6b', '#4ecdc4']
                  }]
                }}
                options={{
                  ...commonChartOptions
                }}
              />
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default Dashboard;
