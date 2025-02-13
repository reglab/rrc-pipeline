import React from "react";
import { Col, Container, Row } from "react-bootstrap";
import { Link, Route, Routes } from "react-router-dom";

import ProxyPatternsCard from "./components/ProxyPatternsCard";

import "bootstrap/dist/css/bootstrap.min.css";
import "./App.css";

const App: React.FC = () => {
  return (
    <Container fluid className="app-container">
      <Row className="header">
        <Col className="text-center py-3">
          <h1 className="app-title">
            <Link to="/" className="text-decoration-none">
              Blank
            </Link>
          </h1>
        </Col>
      </Row>
      <Container className="main-content">
        <Row>
          <Col>
            <Routes>
              <Route path="/" element={<ProxyPatternsCard />} />
            </Routes>
          </Col>
        </Row>
      </Container>
    </Container>
  );
};

export default App;
